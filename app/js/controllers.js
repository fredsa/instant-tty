'use strict';

/* Controllers */

angular.module('myApp.controllers', [])

.controller('AlertController', ['$scope', 'Alert', function($scope, Alert) {
  $scope.alerts = Alert.alerts;

  $scope.closeAlert = function(idx) {
    Alert.remove_alert(idx);
  };

  $scope.$on('$routeChangeStart', function() {
    Alert.clear();
    Alert.info('Loading...');
  });

  $scope.$on('$routeChangeSuccess', function() {
    Alert.clear();
  });
}])

.controller('OAuth2Controller', ['$scope', '$http', '$location', '$timeout', function($scope, $http, $location, $timeout) {
  $scope.status = "OAuth2Controller initial state";
  // $scope.config = config;

  function _params2hash(params) {
    var map = {};
    angular.forEach(params.split('&'), function(param) {
      var kv = param.split('=');
      map[kv[0]] = kv[1];
    });
    return map;
  }

  $scope.$on('$routeChangeSuccess', function() {
    // access_token, token_type, expires_in
    var map = _params2hash($location.hash());
    var access_token = map.access_token;
    console.log('access_token', access_token )
    $http.post('/api/oauth2', map)
    .success(function() {
      // console.log('BEFORE', $scope.config)
      // delete $scope.config.oauth2_url;
      // console.log('AFTER', $scope.config)
      $scope.status = "Thank you. OAuth2 access token has been set. Redirecting...";
      $timeout(function() {
        $location.path('/').hash('');
      }, 1000);
    })
  });

  $scope.hash = function() {
    return $location.hash();
  }

}])

.controller('MainController', ['$scope', '$http', '$window', '$location', 'config', function($scope, $http, $window, $location, config) {
  $scope.status = "Awaiting your command";
  $scope.config = config;

  $scope.$on('$routeChangeSuccess', function() {
    // http://localhost:8080/#access_token=ya29.1.AADt....&token_type=Bearer&expires_in=3600
    if (config.oauth2_url) {
      $window.location.href = config.oauth2_url;
    } else {
      $scope.newinstance();
    }
  });

  $scope.newinstance = function() {
    $scope.status = "Requesting instance...";
    $http.post('/api/instance')
    .success(function(data, status, headers, config) {
      $scope.status = "Got instance: " + data.instance_name;
    });
  }
}]);
