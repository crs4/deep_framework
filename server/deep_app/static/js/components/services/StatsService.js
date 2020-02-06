'use strict';
var angular = require('../../../node_modules/@bower_components/angular')
angular.module('app')
      .service('statsService', [
    statsService
]);

function statsService(){
  var data = {};
  var source = new EventSource('/api/stats');
  return {
     get_data: function(callback) {
       source.addEventListener("message", callback, false);
     }
  }; 
  


}
