var app = angular.module('MyApp', []);
app.controller('MyController', function ($scope, $http, $window) {
	$scope._mainframe = document.getElementById("view_iframe");
	$scope._editrame = document.getElementById("edit_iframe");
	
	$scope.view = null;

	$scope._mainframe.onload= function() {
		$scope.$apply(function() {
			$scope.loading = false;
			$scope.needsRefresh = false;
		});
	}
	
	$scope.loading = false;
	$scope.modified = false;
	$scope.editing = false;
	$scope.needsRefresh = false;
	
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
	    				$scope.modified = true;
	    			});
	    		});
		    };
		    $scope._editrame.src = "content/edit";
		}
//		else if(!$scope.editing && $scope.needsRefresh){
//			//if we close the editor and we did not refresh, do it now:
//			$scope.refreshView();
//		}
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
			  	$scope.needsRefresh = response.data.needs_build;
			  	$scope.aceEditor.session.getUndoManager().markClean();
			  },
			  function(response){ // failure callback
				console.log("failed saving");  //FIXME: handle failure
			  }
	    );
    }
    
	$scope.setView = function(value){  // value can be 'html' or 'pdf
		if(value === $scope.view && !$scope.needsRefresh){
			return;
		}
		
		$scope.loading = true;
		$scope.view = value;
		$scope.needsRefresh = false; //due to current html page view design we need to add it now
		//if we change the behaviour, then this line might be deleted cause in any case
		//needsRefresh is set to false on iframe load (see above)
		
		// seems that sometimes browsers have cache, so, for safety:
		var append = "?preventcache=" + Date.now()
		$scope._mainframe.src = "content/" + value + append;
	
		// this should not suffer of cache:
		// $scope._mainframe.contentWindow.location.reload(true);
		// Unfortunately, if we cannot call it unless
		// the url needs to be refreshed. Give up cause handling all cases is a mess. For info
		// anyway:
		// http://stackoverflow.com/questions/13477451/can-i-force-a-hard-refresh-on-an-iframe-with-javascript
	};
	
	$scope.setView('html');

});