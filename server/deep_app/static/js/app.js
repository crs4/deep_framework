'use strict'

var angular = require('../node_modules/@bower_components/angular')
var app = angular.module('app', ['ngMaterial'])
var deepApp = angular.module('deepApp', ['ngAnimate', 'ngCookies',
    'ngSanitize', 'ui.router', 'ngMaterial', 'nvd3', 'app', 'md.data.table', 'ngFileSaver'])

// module.exports = 'app';

