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

    trustedHtmlError: function(htmlmsg) {
      alert_list.push({type: 'error', icon: 'icon-exclamation-sign', htmlmsg: htmlmsg});
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

.factory('appHttpInterceptor', ['$q', '$log', '$window', '$sce', 'Alert' ,function($q, $log, $window, $sce, Alert) {
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
      if (err.status && err.headers && err.headers('X-App-Error')) {
        if (err.status == 408) {
          Alert.info(err.data['app-error']);
        } else {
          Alert.error('App Error ' + err.status + ': ' + err.data['app-error']);
        }
      } else if (err.status && err.headers && err.headers('Content-Type').indexOf('text/html') == 0) {
        // TODO: handle App Engine's default HTML tracebacks with $sce.trustAs
        Alert.trustedHtmlError($sce.trustAsHtml(err.data));
      } else if (err.status && err.config && err.data) {
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
  $http.get('/api/config').then(function(response) {
    deferred.resolve(response.data);
  }, function() {
    deferred.reject('There was a problem fetching the config');
  });
  return deferred.promise;

  // return $http.get('/api/config');
}]);

