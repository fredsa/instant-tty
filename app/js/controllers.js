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

.controller('ChannelController', ['$scope', '$log', 'appConfig', function($scope, $log, appConfig) {
  var INITIAL_RETRY_DELAY_MS = 500;

  var retry_delay_ms = INITIAL_RETRY_DELAY_MS;

  $scope.messages = [];

  appConfig.then(function(config) {
    $scope.config = config;
    $scope.$emit('channel_token', config.channel_token);
  });

  $scope.$on('channel_token', function(evt, channel_token) {
    var channel = new goog.appengine.Channel(channel_token);
    var socket = channel.open();
    socket.onopen = $scope.onopen;
    socket.onclose = $scope.onclose;
    socket.onerror = $scope.onerror;
    socket.onmessage = $scope.onmessage;
  });

  $scope.onopen = function() {
    // $log.debug('socket.onopen()');
    retry_delay_ms = INITIAL_RETRY_DELAY_MS;
    $scope.$apply();
  };

  $scope.onclose = function() {
    // $log.debug('socket.onclose()');
    maybe_open_socket_with_backoff();
    $scope.$apply();
  };

  $scope.onerror = function(err) {
    // expect err.code and err.description to be set
    // err.description values include 'Invalid+token.' and 'Token+timed+out.'
    $log.debug('socket.onerror(', err, ')');
    maybe_open_socket_with_backoff();
    $scope.$apply();
  };

  $scope.onmessage = function(msg) {
    // $log.debug('socket.onmessage(', msg, ')');
    $scope.messages.push(msg.data);
    $scope.$apply();
  }
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

.controller('MainController', ['$scope', '$log', '$http', '$window', '$location', '$timeout', 'Alert', 'config', function($scope, $log, $http, $window, $location, $timeout, Alert, config) {
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

  $scope.openwindow = function() {
    $window.open($scope.term_url);
  }

  $scope.newinstance = function() {
    $scope.status = 'Creating a scratch Compute Engine VM...';
    $http.post('/api/instance')
    .success(function(data, status, headers, config) {
      $scope.$emit('channel_token', data.instance_name);
      $scope.status = 'Instance ' + data.instance_name +
                      ' with IP address ' + data.external_ip_addr +
                      ' is ready.'
      $scope.term_url = 'http://' + data.external_ip_addr +
                        '/#' + data.plaintext_secret;
    })
    .error(function(data, status, headers, config) {
      // TODO: Exponential backoff
      var delay = 3;
      $scope.status = 'Will try again in ' + delay + ' seconds.';
      $timeout(function() {
        Alert.clear();
        $scope.newinstance();
      }, delay * 1000);
    });
  }
}]);
