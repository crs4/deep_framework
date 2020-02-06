'use strict';
var angular = require('../../../node_modules/@bower_components/angular')
angular.module('app')
      .service('algService', [
    '$http',
    algService
]);

function algService($http){

  this.get_algs = function(){
    return $http.get("/api/algs").then(function(response){
      return response.data;
    });
  }
  


}
