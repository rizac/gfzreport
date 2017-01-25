var app = angular.module('MyApp', []);
app.controller('MyController', function ($scope, $http, $window) {
	$scope._init = true; //basically telling setView to update the commits only the first time
	$scope._VIEWS = ['html', 'pdf'];
	$scope.view = null;  // the current view null for the moment
	
	// note: needsRefresh means: true: request the server, false: display what's in the iframe
	// (if the page has really to be refreshed - e.g.e built, is up to the server)
	// pdfs could be quite heavy so we don't want to download them all the time
	$scope.needsRefresh = {};
	$scope.frames = {'edit': document.getElementById("edit_iframe")};

	// setting up frames and needsRefresh. The two obects above have $scope._VIEWS as keys.
	// Note that we avoid closure with forEach
	// http://stackoverflow.com/questions/750486/javascript-closure-inside-loops-simple-practical-example
	$scope._VIEWS.forEach(function(_view) {
		  // ... code code code for this one element
		$scope.needsRefresh[_view] = true;
		var frame = document.getElementById(_view + "_iframe");  // e.g. 'html_iframe'
		// add listener on load complete:
		frame.onload = function() {
			$scope.$apply(function() {
				$scope.needsRefresh[_view] = false;
				$scope.loading = false;
				if ($scope._init){  // we need to update commits only the first load, after it 
					//will be managed by saving the document from within the app
					$scope.getCommits(); //therein we will set $scope._init = false;
				}
			});
		};
		$scope.frames[_view] = frame;
	});

	
	$scope.loading = false;
	$scope.modified = false;
	$scope.editing = false;
	
	$scope.aceEditor = null;  //this will be set to an object after we init editing the first time
	$scope.toggleEdit = function(){
		$scope.editing = !$scope.editing;
		if ($scope.editing && !$scope.aceEditor){
			//$scope.loading = true;
			var iframe =  $scope.frames['edit'];
			iframe.onload= function() {
		        //$scope.loading = false;
		        $scope.aceEditor = iframe.contentWindow.editor;
	    		//add listener WHEN LOADED:
	    		$scope.aceEditor.on("input", function() {
	    			$scope.$apply(function() {
	    				var cmts = $scope.commits;
	    				// we might be here if we are modifying the text via keyboard, or if
	    				// we want to view an old commit. In the latter, do not set the editor
	    				// as modified, as we have a copy on the server: the user must modify the
	    				// text by himself if he/she wants to save the content
	    				if (cmts._selIndexRemainder > -1){
	    					// we are viewing an old commit
	    					$scope.modified = false;
	    				}else{
	    					// we are really modifying the editor
	    					$scope.modified = true;
	    				}
	    				cmts.selIndex = cmts._selIndexRemainder;
	    				cmts._selIndexRemainder = -1;
	    			});
	    		});
		    };
		    iframe.src = "content/edit";
		}
	};
	
    $scope.save = function(){
    	if (!$scope.aceEditor){
    		return;
    	}
    	$http.post('save', JSON.stringify({source_text: $scope.aceEditor.getValue() }),
	    		   {headers: { 'Content-Type': 'application/json' }}
    	).then(
    			function(response){ // success callback
		    		$scope.modified = false;
				  	$scope.aceEditor.session.getUndoManager().markClean();
				  	$scope._setCommits(response.data || []);
		    	},
		    	function(response){ // failure callback
		    		console.log("failed saving");  //FIXME: handle failure
				}
    	);
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
		$scope.needsRefresh[view] = false; //due to current html page view design we need to add it now
		//if we change the behaviour, then this line might be deleted cause in any case
		//needsRefresh is set to false on iframe load (see above)
		var frame = $scope.frames[view]
		// seems that sometimes browsers have cache, so, for safety:
		var append = "?preventcache=" + Date.now()
		frame.src = "content/" + view + append;
	
		// As a remainder. If the url is already set, one could use also:
		// iframe.contentWindow.location.reload(true);
		// (http://stackoverflow.com/questions/13477451/can-i-force-a-hard-refresh-on-an-iframe-with-javascript)
	};
	
	$scope.commits = {data:[], selIndex: -1, _selIndexRemainder: -1};
	$scope.getCommits = function(){
		$http.post(
				'get_commits', JSON.stringify({}), {headers: { 'Content-Type': 'application/json' }}
			).then(
	    		function(response){ // success callback
	    			$scope._setCommits(response.data || []);
	    		},
	    		function(response){ // failure callback
	    			console.log("failed getting commits");  //FIXME: handle failure (weel this should be silently ignored)
	    		}
	    );
	}
	
	$scope._setCommits = function(commitsArray){
		// set commits is called at startup AFTER setting the view
		// (cause we might have to git-init or update stuff and we want the commits to be in synchro)
		// and as the response after saving.
		// if at startup, do not mark views as dirty (needsRefresh)
		var cmts = $scope.commits;
		if($scope._init){
			$scope._init = false;
		}else if (cmts.length != commitsArray.length || (!commitsArray.length) || (cmts[0] != commitsArray[0])){
			for (var i=0; i < $scope._VIEWS.length; i++){
				$scope.needsRefresh[$scope._VIEWS[i]] = true;
			}
		}
		cmts.data = commitsArray;
		cmts.selIndex = 0; //as returned from server `git` command (0=last)
		cmts._selIndexRemainder = -1;
	};
	
	$scope.currentCommit = function(hash){
		var cmts = $scope.commits;
		if (hash === undefined){ // called with no argument, return current commit or null
			if (!cmts.data || cmts.selIndex<0){
				return null;
			}
			return cmts.data[cmts.selIndex];
		}
		
		$http.post('get_source_rst', 
	    		   JSON.stringify({'commit_hash': hash}),
	    		   {headers: { 'Content-Type': 'application/json' }}
	    	).then(
	    		function(response){ // success callback
    			   $scope.aceEditor.setValue(response.data, 1);  // 1: moves cursor to the start
    			   cmts.selIndex = -1;
    			   for( var i=0 ;i < cmts.data.length; i++){
    					if (cmts.data[i].hash == hash){
    						cmts.selIndex = i;
    						break;
    					}
    				}
    				
    				// Changes in the editor text (aceEditor.on('input',...) see above) notify
    				// a function listener F (see above) which sets
    				// some flags (e.g. $scope.modified=true and $scope.commitIndex=-1).
    				// We might set here the new commitIndex (most likely not -1), *but*
    				// F is called after timeout,
    				// (and only once if we do several changes quickly), so we
    				// need to set a $scope "hidden" variable to be checked inside F
    			   cmts._selIndexRemainder = cmts.selIndex;
	    		},
	    		function(response){ // failure callback
	    			console.log("failed getting commits");  //FIXME: handle failure (weel this should be silently ignored)
	    		}
	    	);
	}

	var popups = {commits: false, addFig: false, figLabel: ''};
	
	$scope.addFigure = function(){
		var elm = document.getElementById('upload-file');
		var formData = new FormData(elm);
		// from http://stackoverflow.com/questions/13963022/angularjs-how-to-implement-a-simple-file-upload-with-multipart-form
		// Angularjs (1.0.6, but apparently also 1.5.6) does not support ng-model on "input-file"
		// tags so you have to do it in
		// a "native-way" that pass the all (eventually) selected files from the user.
		var files = elm.querySelector('#flupld_').files;
		formData.append('file', files[0]);
		// post and see if it worked
		$http.post('upload_file',  formData,{headers: {'Content-Type': undefined },  // let angular guess the type (it works!)
	        								 transformRequest: angular.identity})
	    .then(
	    	function(response){ // success callback
	    		// $scope.aceEditor.setValue(response.data, 1);  // 1: moves cursor to the start
	    		var text = response.data;
	    		var editor = $scope.aceEditor;
	    		var edSession = editor.session;
	    		// detect position of end:
	    		var row = edSession.getLength() - 1
	    		var column = edSession.getLine(row).length // or simply Infinity
	    		edSession.insert({
	    		   row: edSession.getLength(),
	    		   column: 0
	    		}, "\n\n" + text + "\n\n");
	    		// select added text:
	    		var edSelection = editor.selection;
	    		edSelection.setSelectionAnchor(row+1, 0);
	    		var row = edSession.getLength() - 1
	    		var column = edSession.getLine(row).length // or simply Infinity
	    		edSelection.selectTo(row, column);
	    		
	    		// editor.selection.moveCursorTo(row+1, 0, false);
	    		// editor.selection.selectFileEnd();
	    		editor.renderer.scrollSelectionIntoView();
	    	},
	    	function(response){ // failure callback
	    		console.log("failed getting commits");  //FIXME: handle failure (weel this should be silently ignored)
	    	}
	    );
	}
	
	$scope.setView('html');

});