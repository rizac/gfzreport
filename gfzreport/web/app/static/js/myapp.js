var app = angular.module('MyApp', []);
app.controller('MyController', function ($scope, $http, $window, $timeout, $rootScope) {
	$scope._init = true; //basically telling setView to update the commits only the first time
	$scope._VIEWS = ['html', 'pdf'];
	$scope.view = null;  // the current view null for the moment

	// note: needsRefresh means: false: display what's in the iframe; true: request the server 
	// (if the page has really to be refreshed - e.g.e built, is up to the server).
	// Pdfs could be quite heavy so we don't want to download them all the time
	$scope.needsRefresh = {};
	$scope.frames = {'edit': document.getElementById("edit_iframe")};
	$scope.buildExitcode = {};  //same keys as needsRefresh (the views) mapped to an int representing the last build exit code
	$scope.scrollY = {}; // see above. Stores the page scrollY to reset it after the build

	// setting up frames and needsRefresh. The two obects above have $scope._VIEWS as keys.
	// Note that we avoid closure with forEach
	// http://stackoverflow.com/questions/750486/javascript-closure-inside-loops-simple-practical-example
	$scope._VIEWS.forEach(function(_view) {
		$scope.needsRefresh[_view] = true;
		$scope.buildExitcode[_view] = -1;
		$scope.scrollY[_view] = 0;
		var frame = document.getElementById(_view + "_iframe");  // e.g. 'html_iframe'
		// add listener on load complete:
		frame.onload = function() {
			$scope.$apply(function() {
			    // first make all anchors within the html with target = blank, otherwise
			    // they open inside the iframe:
			    // we prefer to make it from here so we do not change each template:
			    if (_view == $scope._VIEWS[0]){ //is html page
			        // small delay to be sure page has loaded:
    			    frame.contentWindow.setTimeout(function(){
    			        var anchors = frame.contentWindow.document.querySelectorAll('a[href^="http"]'); //'a[href^="http://"],a[href^="https://"]');
    			        for (var i = 0; i < anchors.length; i++) {
    			            anchors[i].setAttribute('target', '_blank');
    			        }
    			    }, 200);
			    }
			    // proceed:
				if ($scope.needsRefresh[_view]){
					$scope.fetchBuildExitcode(_view);
				}
				$scope.needsRefresh[_view] = false;
				$scope.loading = false;
				$scope._init = false; //if first time, notify that everything is loaded succesfully
				if ($scope.scrollY[_view] != 0){
					// to access an iframe window, use (frame.contentWindow || frame)
					// https://stackoverflow.com/questions/16018598/how-to-get-a-reference-to-an-iframes-window-object-inside-iframes-onload-handl
					(frame.contentWindow || frame).scrollTo(0, $scope.scrollY[_view]);
				}
			});
		};
		$scope.frames[_view] = frame;
	});
	
	$scope.fetchBuildExitcode = function(_view){
		$http.post(
    		'last_build_exitcode',
    		JSON.stringify({'buildtype': _view}),
	    	{headers: { 'Content-Type': 'application/json' }}
    	).then(
			function(response){ // success callback
	    		$scope.buildExitcode[_view] = parseInt(response.data);
			},
	    	function(response){ // failure callback
				$scope.buildExitcode[_view] = -1;  //for safety
			}
    	);
	};
	//this is used in ng-class to get the current view exit code
	$scope.getCurrentViewExitcode = function(){
		return $scope.buildExitcode[$scope.view];
	}
	
	$scope.setModified = function(value){
		/**
		 * Sets the $scope.modified flag (which disables some buttons in the view),
		 * the $scope.commitHash if value is true, 
	     * and adds/ removes the "prevent leave dialog box" functionality if modified is True/False.
	     * Although there are 100000 "proper" ways to achieve the same in angular, this low level approach is by far
	     * the simplest and shortest for our use-case. See https://stackoverflow.com/questions/30571951/angularjs-warning-when-leaving-page
		 */
    	$scope.modified = value;
    	if (value){ // if modified, current editor content does not match anymore commitHash,
    		// need to save to fetch the new hash and set it to $scope.commitHash
    		$scope.commitHash = null;
    		// if we are setting modified = false we will set $scope.commitHash after this
    		// function call. See $scope.save and 'iframe.onload' in $scope.toggleEdit
    	}
    	/* the implementation of the onbeforeunload is insane. The following works on Chrome that's enough.
    	 * See _handleUnloadEvent below for details
    	 */
    	var func = $scope._handleUnloadEvent;
    	var win = $window;
    	if (value){
    		win.addEventListener ? win.addEventListener("beforeunload", func): win.attachEvent("onbeforeunload", func);
    	}else{
    		win.removeEventListener ? win.removeEventListener("beforeunload", func) :win.detachEvent("onbeforeunload", func);
    	}
    };
    
    $scope._handleUnloadEvent = function (event) {
    	/**
    	 * this function is called when we are about to leave the page and $scope.modified=True.
    	 * To make the popup appear we need to set event.returnValue' to a non-empty string,
    	 * which is one of the most counter-intuitive things I've ever seen.
    	 * Moreover, the string seems NOT shown anymore in most browsers, we leave it just in case.
    	 * And finally, from here:
    	 * https://developer.mozilla.org/en-US/docs/Web/Events/beforeunload
    	 * they claim  most browser ignore the event return value and close the window anyway, which
    	 * is not true... :D
    	 */
    	var msg = "There are unsaved changes in the editor. Leave anyway?";
    	event.returnValue = msg;
    	return msg;
    };
	
	$scope.loading = false;
	$scope.loadingMsgs = [];
	$scope.setModified(false);
	$scope.editing = false;
	/* commitHash: the commit linked to the current editor content. When initializing the editor
	 * the first time, it is queried to the server. When modifiying the editor, it is set to null,
	 * when saving the editor, it is returned from the server after git commit.
	 * When setting an old commit from the commits popup, its value is simply changed
	 * When commitHash is null, the "history" button is disabled, meaning the editor content has
	 * been modified and does not point to a server commit hash. It can be null also if the server
	 * has an error fetching the last commit (rare but not impossible). When non-null, the
	 * editor content points to a git commit hash, and the history button is clickable (enabled)
	 */
	$scope.commitHash = null;
	$scope.aceEditor = null;  //NOTE: this will be set to an object after we init editing the first time
	$scope.toggleEdit = function(){
		$scope.editing = !$scope.editing;
		if ($scope.editing && !$scope.aceEditor){
			//$scope.loading = true;
			var iframe =  $scope.frames['edit'];
			iframe.onload= function() {
		        //$scope.loading = false;
		        $scope.aceEditor = iframe.contentWindow.editor;
		        
		        // set options:
		        // In case you want more options,type Cmd , or Ctrl ,
		        // and inspect the given element
		        // var elm = document.querySelector('#setUseWrapMode');
		        // But there are
		        // actually listeners and we use them:
		        
		        $scope.aceEditor.getSession().on("changeWrapMode", function(){
		        	// arguments[1] seems to be the aceEditor.getSession()
		        	var val = arguments[1].getUseWrapMode();
		        	console.log(val);
		        });

		        // add command to save via keybinding
		        $scope.aceEditor.commands.addCommand({
		            name: "saveContent",
		            bindKey: {win: "Ctrl-s", mac: "Command-s"},
		            exec: function(editor) {
		            	if ($scope.editing && $scope.modified){
		            		$scope.save();
		            	}
		            }
		        });
		        
	    		//add listener WHEN LOADED:
	    		$scope.aceEditor.on("input", function() {
	    			$scope.$apply(function() {
	    				// If popup commits is showing, we set the editor value from a commit
	    				// thus, as setModified will set $scope.commitHash to null, we have to
	    				// reset it to the current commit:
	    				var commitRemainder = $scope.popups.commits.visible ? $scope.commitHash : null;
	    				$scope.setModified(true);
	    				if (commitRemainder){
	    					$scope.commitHash = commitRemainder;
	    					$scope.popups.commits.hide();
	    				}
	    			});
	    		});
	    		
	    		//only the first time we load the editor, set currentCommitHash
	    		$http.post(
	    	    		'get_last_commit_hash',
	    	    		JSON.stringify({source_text: $scope.aceEditor.getValue() }),
	    		    	{headers: { 'Content-Type': 'application/json' }}
	    	    	).then(
	    				function(response){ // success callback
	    		    		$scope.commitHash = response.data;
	    		    	},
	    		    	function(response){ // failure callback
	    		    		$scope.commitHash = null;
	    				}
	    	    	);
	    		
		    };
		    iframe.src = "edit";
		}
	};
	
	$scope.editorToggleKeyboardShortcuts = function(string){
		if ($scope.editorShowKeyboardShortcuts){
			$scope.aceEditor.execCommand("hideKeyboardShortcuts");
		}else{
			$scope.aceEditor.execCommand("showKeyboardShortcuts");
		}
		$scope.editorShowKeyboardShortcuts = !$scope.editorShowKeyboardShortcuts;
	};
	
	$scope.editorToggleSettingsMenu = function(string){
		if ($scope.editorShowSettingsMenu){
			$scope.aceEditor.execCommand("hideSettingsMenu");
		}else{
			$scope.aceEditor.execCommand("showSettingsMenu");
		}
		$scope.editorShowSettingsMenu = !$scope.editorShowSettingsMenu;
	};
	
	$scope.isEditable = true; //note that if the project is not editable, this flag stays true
	// but it will be useless as the button invoking the function below will be hidden and
	// thus the function below will never be called. Note also that although we implemented
	// a setEditable(value) function, the argument value can only be false currently
	$scope.setEditable = function(value, promptConfirm){
		if(!promptConfirm || 
			confirm('Do you want to lock the report and make it non-editable by any user?')){
			$http.post(
    	    		'set_editable',
    	    		JSON.stringify({editable: value}),
    		    	{headers: { 'Content-Type': 'application/json' }}
    	    	).then(
    				function(response){ // success callback
    					if (!value && $scope.editing){
    						$scope.toggleEdit();
    					}
    					$scope.isEditable=value;
    		    	},
    		    	function(response){ // failure callback
    		    		alert((response.data.message || 'A server error occurred') +
    		    				'\n\nPlease retry later or contact the administrator');
    				}
    	    	);
		}
	};
	
    $scope.save = function(){
    	/**
    	 * Saves the content of the editor on the server, which returns the new commits
    	 * list. The commits list is then passed to $scope._setCommits to update what will
    	 * be shown in the 'commits popup' window
    	 */
    	if (!$scope.aceEditor){
    		return;
    	}
    	$scope.commitHash = null;
    	$http.post(
    		'save',
    		JSON.stringify({source_text: $scope.aceEditor.getValue() }),
	    	{headers: { 'Content-Type': 'application/json' }}
    	).then(
			function(response){ // success callback
	    		$scope.setModified(false);
	    		$scope.commitHash = response.data.commit_hash;
	    		var needsRefresh = response.data.needs_refresh;
			  	$scope.aceEditor.session.getUndoManager().markClean();
			  	if (response.data){
			  		for (var i=0; i < $scope._VIEWS.length; i++){
			  			// if $scope.needsRefresh was previously set to true, leave it to true
			  			// otherwise set it to needsRefresh:
			  			$scope.needsRefresh[$scope._VIEWS[i]] |= needsRefresh;
			  		}
			  	}
			  	//$scope._setCommits(response.data || [], true); //true: do a check to see if we need to refresh the views (pdf, html)
	    	},
	    	function(response){ // failure callback
	    		$scope.showError(response);
			}
    	);
    };
    
    $scope.showError = function(response){
    	$scope.popups.errDialog.show();
    	// show first the popup, cause show() cancels the error message by default
    	$scope.popups.errDialog.errMsg = $scope.exc(response);
    };
    
	$scope.setView = function(view){  // value can be 'html' or 'pdf
		if($scope.loading){
			// this is very DANGEROUS: jumping clicks on the tabs while loading
			// might trigger several build for the same view (e.g., 'html') in the
			// server. So return:
			return;
		}
		if(view === $scope.view && !$scope.needsRefresh[view]){
			return;
		}
		$scope.view = view;
		if(!$scope.needsRefresh[view]){
			return;
		}
		$scope.loading = true;
		//store scrollY to reset it after page load:
		var frame = $scope.frames[view]
		// to access an iframe window, use (frame.contentWindow || frame)
		// https://stackoverflow.com/questions/16018598/how-to-get-a-reference-to-an-iframes-window-object-inside-iframes-onload-handl
		$scope.scrollY[view] = (frame.contentWindow || frame).scrollY;
		// seems that sometimes browsers have cache, so, for safety:
		// var append = "?preventcache=" + Date.now()
		// we implemented nocache mechanism on the backend, so
		// frame.src = view + append;
		frame.src = view;

		// As a remainder. If the url is already set, one could use also:
		// iframe.contentWindow.location.reload(true);
		// (http://stackoverflow.com/questions/13477451/can-i-force-a-hard-refresh-on-an-iframe-with-javascript)
	};
	
	/********************************************************************************************
	 * POPUPS STUFF 
	 ********************************************************************************************/
	
	/** first define our popup data container:
	 * we want an object type reflecting a popup, storing popup properties and that:
	 * can get if it's visible (by default it isn't) easily
	 * can toggle its visibility easily
	 * can store properties like a normal object for eg. ng-model bindings
	 * we implement the props class which will be mapped to any popup defined here:
	 */
	function props(defaults){
		// initialize by setting all our desfaults properties to this object
		var defs = defaults || {};
		for (var d in defs){
			this[d] = defs[d];
		}
		// attach common properties (for the moment, visible and errMsg)
		if (this.visible === undefined){
			this.visible = false;
		}
		if (this.errMsg === undefined){
			this.errMsg = '';
		}
		// methods:
		this.show = function(){
			// make errMsg empty, so that previous errors, if any, do not appear when window shows up (misleading)
			this.errMsg = '';
			this.visible = true;
			if (this.focusElmId){
				var focusElm = $window.document.getElementById(this.focusElmId);
				if (focusElm){
					// needs a timeout because angular will digest the changes and show the element
					// after this function call. And if the element is not visible, the focus does
					// not work:
					$window.setTimeout(function(){focusElm.focus();}, 200);
				}
			}
		};
		this.hide = function(){
			this.visible = false;
		};
		this.toggle = function(){
			// call the respective functions so if there is something to setup in there, we do it
			if (this.visible){
				this.hide();
			}else{
				this.show();
			}
		};
	};
	
	$scope.popups = {
		'errDialog': new props({'title': 'Error', 'errMsg': ''}),
		'commits': new props({'title': 'History (git commits)', 'loading': false,
							  'data':{commits:[], selected: {'commit': null, 'diff': []}},
							  		  // navigation: newest, newer, older, oldest. null:
							  		  // each element is an hash in [commits[0].hash, commits[1].hash,... ]
							  		  'navigation': [null, null, null, null]}),
		'logIn': new props({'title': 'Log in', 'focusElmId': 'login-email'}),
		'addFig': new props({'label': '', 'keepOpen': false, 'title': 'Add figure', 'insertAtCursor': false}),
		'logs': new props({'title': 'Build info (log-file)', 'loading': false, 'showFullLog': false})
	};	
	
	$scope.exc = function(response){
		/**
		 * handle http exception by returning a formatted string message
		 */
		var msg = "";
		if (response.data && response.data.message){  // most exceptions are sent from the client with this field
			// if it's an unknown exception, this should be empty
			msg = response.data.message;
		}
		// if there is no connection status seems to be -1 and statusText empty, so try to help:
		var status = response.status;
		var statusText = response.statusText;
		if(status == -1 && !statusText){
			statusText = "No internet connection?";
		}
		if (msg){
			return msg + " (" + status + ": " + statusText + ")";
		}else{
			return "Error (" + status + ": " + statusText + ")";
		}
		
	};
	
	
	/**
	 * COMMITS POPUP callback(s)
	 */
	$scope.showCommits = function(){
		/**
		 * fetches all commits. This function is called if $scope.commitHash is truthy, as
		 * the button invoking it is enabled only if $scope.commitHash is truthy
		 */
		var commits = $scope.popups.commits;
		commits.loading = true;
		commits.show();
		commits.data.selected.commit = null;
		commits.data.selected.diff = [];
		commits.data.navigation = [null, null, null, null, null];
		$http.post(
			'get_commits',
			JSON.stringify({}),
			{headers: { 'Content-Type': 'application/json' }}
		).then(
    		function(response){ // success callback
    			commits.loading = false;
    			commits.data.commits = response.data || [];
    			$scope.setSelectedCommitInWindow($scope.commitHash);
    		},
    		function(response){ // failure callback
    			commits.errMsg = $scope.exc(response);
    		}
	    );
	}

	$scope.setSelectedCommitInWindow = function(hash){
		/**
		 * This fetches the git diff from the given has vs the latest version.
		 * IT IS ASSUMED THAT 
		 * showCommits HAS BEEN CALLED BEFORE THIS FUNCTION
		 */
		var commits = $scope.popups.commits;
		commits.data.selected.commit = null;
		commits.data.selected.diff = [];
		commits.data.navigation = [null, null, null, null, null];
		$http.post(
			'get_git_diff', 
	    	JSON.stringify({'commit1': $scope.commitHash, 'commit2': hash}),
	    	{headers: { 'Content-Type': 'application/json' }}
    	).then(
    		function(response){ // success callback
    			var diffidx = 1;
    			// split diffs into a set of arrays for visualization
    			// each array element is in turn a tuple:
    			// first element "+", "-" or nothing, second element the diff line of text
    			response.data.forEach(function callback(currentValue, index, array) {
    				var lines = []
    				currentValue.split("\n").forEach(function callback(currentValue, index, array) {
    					var lineType = currentValue.substring(0, 1);
    					var line = currentValue.substring(1).trim();
    					if (!line){
    						line = " "; //preserve div height ...
    					}
    					lines.push([lineType, line]);
        			});
    				commits.data.selected.diff.push(lines);
    			});
    			// setup newest, newer etecetra (navigation):
    			var idx = -1;
    			for (var i = 0; i < commits.data.commits.length; i++){
    				if (commits.data.commits[i].hash == hash){
    					commits.data.selected.commit = commits.data.commits[i];
    					idx = i;
    					break;
    				}
    			}
    			if(idx > -1){
    				var lastIndex = commits.data.commits.length - 1;
    				commits.data.navigation[0] = idx > 0 ? commits.data.commits[0].hash : null;  // newest
    				commits.data.navigation[1] = idx > 0 ? commits.data.commits[idx-1].hash : null;  // newer
    				commits.data.navigation[2] = idx < lastIndex ? commits.data.commits[idx+1].hash : null;
    				commits.data.navigation[3] = idx < lastIndex ? commits.data.commits[lastIndex].hash : null;
    				commits.data.navigation[4] = idx + 1;
    			}
    			
    		},
    		function(response){ // failure callback
    			commits.errMsg = $scope.exc(response);
    		}
    	);
	}

	$scope.setEditorContentFromCommit = function(hash){
		/**
		 * This function sets the editor content from the given commit hash.
		 * IT IS ASSUMED THAT 
		 * showCommits HAS BEEN CALLED BEFORE THIS FUNCTION
		 */
		$http.post(
			'get_source_rst', 
	    	JSON.stringify({'commit_hash': hash}),
	    	{headers: { 'Content-Type': 'application/json' }}
    	).then(
    		function(response){ // success callback
    			$scope.commitHash = hash;
    			$scope.aceEditor.setValue(response.data, 1);  // 1: moves cursor to the start
    			// the command above WILL fire an aceEditor 'input' event
    			// (probably is in a timeout function) which we handle in a listener L
    			// (L = '$scope.aceEditor.on("input", ...' in $scope.toggleEdit). In L we
    			// call $scope.setModified(true), which in turn sets $scope.commitHash = null:
    			// this is ok when we modify the editor "normally" via key events, but here we
    			// want to preserve $scope.commitHash. 
    			// The (not so elegant) way is NOT TO HIDE the popup window here so we will know
    			// in L that $scope.commitHash has not to be set to null
    		},
    		function(response){ // failure callback
    			$scope.popups.commits.errMsg = $scope.exc(response);
    		}
    	);
	}
	
	/**
	 * LOGIN/OUT POPUP(s) callback(s) and data
	 */

	$scope.isLoggedIn = false;
	$scope.logIn = function(){
		// create a FormData object. The FormData gets a Form html elements and will add to it
		// all inputs with a name attribute set
		var elm = document.getElementById('login');
		var formData = new FormData(elm);
		$http.post(
			'login', 
			formData,
			{headers: {'Content-Type': undefined }, transformRequest: angular.identity}  // let angular guess the type (it works!)
		).then(
    		function(response){ // success callback
    			$scope.isLoggedIn=true;
    			$scope.popups.logIn.hide();
    			//load commits now:
    			//$scope.fetchCommits();
    		},
    		function(response){ // failure callback
    			$scope.isLoggedIn=false; // for safety
    			$scope.popups.logIn.errMsg = $scope.exc(response);
    		}
    	);
	};

	$scope.logOut = function(){
		function doLogout(response){
			$scope.isLoggedIn = false; //should hide editor if visible
    		$scope.setView('html'); //if we are on the pdf, restore the html view. This forces a rebuild if needed
    		for(var k in $scope.popups){ //hide all popups
    			$scope.popups[k].hide();
    		}
		};
		$http.post('logout', 
			JSON.stringify({}),
	    	{headers: { 'Content-Type': 'application/json' }}
	    ).then(
    		doLogout, // success callback
    		doLogout // failure callback (there might be a way to write doLogout only once like a 'finally' clause, too lazy to search for it)
    	);
	};
	
	/**
	 * ADD FIGURE POPUP callback(s) and data
	 */
	
	$scope.addFigure = function(){
		// create a FormData object. The FormData gets a Form html elements and will add to it
		// all inputs with a name attribute set
		var elm = document.getElementById('upload-file');
		var formData = new FormData(elm);
		// BUT: from http://stackoverflow.com/questions/13963022/angularjs-how-to-implement-a-simple-file-upload-with-multipart-form
		// Angularjs (1.0.6, but apparently also 1.5.6) does not support ng-model on "input-file"
		// tags so you have to do it in
		// a "native-way" that pass the all (eventually) selected files from the user.
		var files = elm.querySelector('#flupld_').files;
		formData.append('file', files[0]);
		
		var insertAtCursor = $scope.popups.addFig.insertAtCursor;
		// post and see if it worked
		$http.post(
			'upload_file',
			formData,
			{headers: {'Content-Type': undefined }, transformRequest: angular.identity} // let angular guess the type (it works!)
	    ).then(
	    	function(response){ // success callback
	    		// $scope.aceEditor.setValue(response.data, 1);  // 1: moves cursor to the start
	    		var text = response.data;
	    		var editor = $scope.aceEditor;
	    		var edSession = editor.session;
	    		var prevRowCount = edSession.getLength();
	    		if (insertAtCursor){
	    			// insert where the cursor is, at the beginning of the line
	    			var cursor = editor.selection.getCursor();
	    			var row = cursor.row;
	    			//var column = cursor.column;
	    		}else{
	    			// detect position of end:
	    			var row = prevRowCount;
	    			//var column = edSession.getLine(row).length // or simply Infinity
	    		}
	    		var textToInsert = "\n\n" + text + "\n\n";
	    		edSession.insert({
	    		   row: row,
	    		   column: 0
	    		}, textToInsert);
	    		// select added text:
	    		var edSelection = editor.selection;
	    		edSelection.setSelectionAnchor(row, 0);
	    		//var row = edSession.getLength() - 1
	    		//var column = edSession.getLine(row).length // or simply Infinity
	    		var rowsAdded = edSession.getLength() - prevRowCount;
	    		if (rowsAdded > 0){
	    			var newRowIndex = row + rowsAdded -1;
	    			edSelection.selectTo(newRowIndex, edSession.getLine(newRowIndex).length);
	    		}
	    		// editor.selection.moveCursorTo(row+1, 0, false);
	    		// editor.selection.selectFileEnd();
	    		editor.renderer.scrollSelectionIntoView();
	    		
	    		if (!$scope.popups.addFig.keepOpen){
	    			$scope.popups.addFig.hide();
	    		}
	    	},
	    	function(response){ // failure callback
	    		$scope.popups.addFig.errMsg = $scope.exc(response);
	    	}
	    );
	}
	
	/**
	 * LOGS POPUP callback(s) and data (note logs are the build logs (sphinx + pdflatex) not the login/out functionality!
	 * Build logs are loaded in a $scope variable to
	 * bind them to the view
	 * But for safety, they are loaded as new data every time we click on the commits/history button
	 */

	$scope.logs = [];  // a two element array: first is the text with the full log, second with errors only (if any)
	$scope.showLogs = function(){
		$scope.popups.logs.loading = true;
		$scope.logs = ['Log file not found', 'Log file not found'];
		$scope.popups.logs.show();
		$http.post(
			'get_logs', 
			JSON.stringify({'buildtype': $scope.view}),
	    	{headers: { 'Content-Type': 'application/json' }}
    	).then(
    		function(response){ // success callback
    		   // response.data is a dict
    			$scope.popups.logs.loading = false;
    			if (response.data[0] || response.data[1]){
    				$scope.logs = response.data;
    			}
    		},
    		function(response){ // failure callback
    			$scope.popups.logs.errMsg = $scope.exc(response);
    		}
    	);
	}

	/**
	 * FINALLY, SETUP THE INITIAL VIEW:
	 */
	
	$scope.setView('html');
});
