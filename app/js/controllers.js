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
  $scope.status = 'Requesting API access...';

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
    $http.post('/api/oauth2', map)
    .success(function() {
      // console.log('BEFORE', $scope.config)
      // delete $scope.config.oauth2_url;
      // console.log('AFTER', $scope.config)
      $scope.status = 'API access token received. Loading...';
      $timeout(function() {
        $location.path('/').hash('');
      }, 1000);
    })
  });

  $scope.hash = function() {
    return $location.hash();
  }

}])

.controller('MainController', ['$scope', '$http', '$window', '$location', '$timeout', 'Alert', 'config', function($scope, $http, $window, $location, $timeout, Alert, config) {
  $scope.status = 'Loading...';
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
    $scope.status = 'Requesting instance...';
    $http.post('/api/instance')
    .success(function(data, status, headers, config) {
      $scope.status = 'Opening a new window to ' + data.instance_name +
                      ' with IP address ' +  data.external_ip_addr;
      $window.open('http://' + data.external_ip_addr);
    })
    .error(function(data, status, headers, config) {
      // TODO: Exponential backoff
      var delay = 2;
      console.log('data',data)
      console.log('status',status)
      $scope.status = 'Will try again in ' + delay + ' seconds.';
      $timeout(function() {
        Alert.clear();
        $scope.newinstance();
      }, delay * 1000);
    });
  }
}]);
