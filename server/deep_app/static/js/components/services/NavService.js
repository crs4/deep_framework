'use strict';
var angular = require('../../../node_modules/@bower_components/angular')
angular.module('app')
        .service('navService', [
        '$q',
        navService
]);

function navService($q){
  var menuItems = [
    {
      name: 'Controls',
      icon: 'build',
      sref: '.controls'
    },
    {
      name: 'Dashboard',
      icon: 'dashboard',
      sref: '.dashboard'
    },
    {
      name: 'Viewer',
      icon: 'visibility',
      sref: '.viewer'
    },
    {
      name: 'API Docs',
      icon: 'menu_book',
      sref: '.docs'
    }
  ];

  return {
    loadAllItems : function() {
      return $q.when(menuItems);
    }
  };
}
