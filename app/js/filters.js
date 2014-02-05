'use strict';

/* Filters */

angular.module('myApp.filters', [])

.filter('tail', [function() {
  return function(arr, count) {
    return arr.slice(-count);
  };
}]);
