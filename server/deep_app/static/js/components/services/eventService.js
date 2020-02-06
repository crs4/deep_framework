'use strict';
var angular = require('../../../node_modules/@bower_components/angular')
angular.module('app')
      .service('eventService', [
    eventService
]);

function eventService(){
  var data = {};
  // var source = new EventSource('/events');
  return {
     get_data: function(callback) {
      //  source.addEventListener("message", callback, false);
     }
  }; 
  


}
