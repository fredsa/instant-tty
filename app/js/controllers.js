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

.controller('MainController', ['$scope', '$http', 'config', function($scope, $http, config) {
  $scope.status = "Awaiting your command";
  $scope.config = config;

  $scope.newinstance = function() {
    $scope.status = "Requesting instance...";
    $http.post('/api/instance')
    .success(function(data, status, headers, config) {
      $scope.status = "Got instance: " + data.instance_name;
    });
  }

  $scope.newinstance();
}]);
