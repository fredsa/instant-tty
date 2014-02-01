'use strict';

/* Services */

angular.module('myApp.services', [])

.factory('Alert', [function() {
  var alert_list = [];

  var Alert = {
    alert_list: alert_list,

    clear: function() {
      alert_list = [];
    },

    handle_exception: function(exception, cause) {
      var msg = '' + exception;
      if (cause) {
        msg += ' caused by ' + cause;
      }
      alert_list.push({type: 'error', icon: 'icon-exclamation-sign', msg: msg});
    },

    note: function(msg) {
      alert_list.push({icon: 'icon-hand-right', msg: msg});
    },

    info: function(msg) {
      alert_list.push({type: 'info', icon: 'icon-info-sign', msg: msg});
    },

    success: function(msg) {
      alert_list.push({type: 'success', icon: 'icon-ok', msg: msg});
    },

    error: function(msg) {
      alert_list.push({type: 'error', icon: 'icon-exclamation-sign', msg: msg});
    },

    alerts: function() {
      return alert_list;
    },

    remove_alert: function(idx) {
      alert_list.splice(idx, 1);
    },

  };

  return Alert;
}])

.factory('appHttpInterceptor', ['$q', '$log', '$window', 'Alert' ,function($q, $log, $window, Alert) {
  return {
    'request': function(config) {
      return config || $q.when(config);
    },

   'requestError': function(response) {
      return $q.reject(response);
    },

    'response': function(response) {
      return response || $q.when(response);
    },

   'responseError': function(err) {
    console.log('err',err)
      if (err.status && err.headers && err.headers('X-App-Error')) {
        Alert.error('X-App-Error HTTP ' + err.status + '\n' + dump(err.data));
      } if (err.status && err.config && err.data) {
        Alert.error('$http ' + err.status + ' ERROR:\n' + dump(err.data) +
                    '\nWITH CONFIG:\n' + dump(err.config));
      } else {
        Alert.error('REPONSE ERROR:\n' + dump(err));
      }
      return $q.reject(err);
    }
  };
}])

.factory('appConfig', ['$http', '$q', '$timeout', function($http, $q, $timeout) {
  var deferred = $q.defer();
  // $timeout(function() {
  //   deferred.resolve('foo');
  // }, 5000);
  // return deferred.promise;

  $http.get('/api/config').then(function(response) {
    deferred.resolve(response.data);
  }, function() {
    deferred.reject('There was a problem fetching the config');
  });
  return deferred.promise;

  // return $http.get('/api/config');
}]);

