var app = angular.module('MyApp', []);
app.controller('MyController', function ($scope, $http, $window) {
	$scope._htmlframe = document.getElementById("viewhtml_iframe");
	$scope._pdfframe = document.getElementById("viewpdf_iframe");
	$scope._editrame = document.getElementById("edit_iframe");
	
	$scope.view = null;
	$scope.needsRefresh = {'html': true, 'pdf': true};
	$scope.frames = {'html': document.getElementById("html_iframe"),
					 'pdf': document.getElementById("pdf_iframe")};
	
	// http://stackoverflow.com/questions/750486/javascript-closure-inside-loops-simple-practical-example
	['html', 'pdf'].forEach(function(arrayElement) {
		  // ... code code code for this one element
		  var frame = $scope.frames[arrayElement];
		  frame.onload = function() {
				$scope.$apply(function() {
					$scope.loading = false;
					$scope.needsRefresh[arrayElement] = false;
				});
			};
		});

	
	$scope.loading = false;
	$scope.modified = false;
	$scope.editing = false;
	
	$scope.aceEditor = null;  //this will be set to an object after we init editing the first time
	$scope.toggleEdit = function(){
		$scope.editing = !$scope.editing;
		if ($scope.editing && !$scope.aceEditor){
			//$scope.loading = true;
			var iframe = $scope._editrame;
			iframe.onload= function() {
		        //$scope.loading = false;
		        $scope.aceEditor = iframe.contentWindow.editor;
	    		//add listener WHEN LOADED:
	    		$scope.aceEditor.on("input", function() {
	    			$scope.$apply(function() {
	    				// we might be here if we are modifying the text via keyboard, or if
	    				// we want to view an old commit. In the latter, do not set the editor
	    				// as modified, as we have a copy on the server: the user must modify the
	    				// text by himself if he/she wants to save the content
	    				if ($scope._commitIndexRemainder > -1){
	    					// we are viewing an old commit
	    					$scope.modified = false;
	    				}else{
	    					// we are really modifying the editor
	    					$scope.modified = true;
	    				}
	    				$scope.commitIndex = $scope._commitIndexRemainder;
	    				$scope._commitIndexRemainder = -1;
	    			});
	    		});
		    };
		    $scope._editrame.src = "content/edit";
		}
	};
	
    $scope.save = function(){
    	if (!$scope.aceEditor){
    		return;
    	}
    	$http.post('save',  //no starting slashes, make it relative to this page.
    			// $scope._ID is defined in
    			//the view (see ng-init)
	    		   JSON.stringify({source_text: $scope.aceEditor.getValue() }),
	    		   {headers: { 'Content-Type': 'application/json' }}
	    		   )
	    .then(function(response){ // success callback
			  	$scope.modified = false;
			  	var needRefr = response.data.needs_build;
			  	$scope.needsRefresh = {'html': needRefr, 'pdf': needRefr};
			  	$scope.aceEditor.session.getUndoManager().markClean();
			  },
			  function(response){ // failure callback
				console.log("failed saving");  //FIXME: handle failure
			  }
	    );
    }
    
	$scope.setView = function(view){  // value can be 'html' or 'pdf
		if($scope.loading){
			// this is harmful: jumping clicks on the tabs while loading
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
	
		// this should not suffer of cache:
		// $scope._mainframe.contentWindow.location.reload(true);
		// Unfortunately, if we cannot call it unless
		// the url needs to be refreshed. Give up cause handling all cases is a mess. For info
		// anyway:
		// http://stackoverflow.com/questions/13477451/can-i-force-a-hard-refresh-on-an-iframe-with-javascript
	};
	
	$scope.commits = [];
	$scope.commitIndex = -1;
	$scope._commitIndexRemainder = -1;
	$http.post('get_commits',  //no starting slashes, make it relative to this page.
			// $scope._ID is defined in
			//the view (see ng-init)
    		   JSON.stringify({}),
    		   {headers: { 'Content-Type': 'application/json' }}
    		   )
    		   .then(function(response){ // success callback
    			   $scope.commits = response.data || [];
    			   $scope.commitIndex = 0; //as returned from server (`git` command)
    			  },
    			  function(response){ // failure callback
    				console.log("failed getting commits");  //FIXME: handle failure (weel this should be silently ignored)
    			  }
    		   );

	$scope.currentCommit = function(hash){
		if (hash === undefined){ // called with no argument, return current commit or null
			if (!$scope.commits || $scope.commitIndex<0){
				return null;
			}
			return $scope.commits[$scope.commitIndex];
		}
		
		$http.post('get_source_rst',  //no starting slashes, make it relative to this page.
				// $scope._ID is defined in
				//the view (see ng-init)
	    		   JSON.stringify({'commit_hash': hash}),
	    		   {headers: { 'Content-Type': 'application/json' }}
	    		   )
	    		   .then(function(response){ // success callback
	    			   $scope.aceEditor.setValue(response.data, 1);  // 1: moves cursor to the start
	    			   var commitIndex = -1;
	    			   for( var i=0 ;i <$scope.commits.length; i++){
	    					if ($scope.commits[i].hash == hash){
	    						commitIndex = i;
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
	    			   	$scope._commitIndexRemainder = commitIndex;
	    			  },
	    			  function(response){ // failure callback
	    				console.log("failed getting commits");  //FIXME: handle failure (weel this should be silently ignored)
	    			  }
	    		   );
		
		
		
	}

	$scope.historyIsShowing = false;
	$scope.showHistory = function(val){
		$scope.historyIsShowing = true && val;
	};

	
	$scope.setView('html');
	
});