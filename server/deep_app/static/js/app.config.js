var angular = require('../node_modules/@bower_components/angular')
require('./app')

angular
    .module('deepApp')
    .config(function ($stateProvider, $urlRouterProvider, $mdThemingProvider,
        $mdIconProvider) {

        $stateProvider
            .state('home', {
                url: '',
                templateUrl: 'static/js/views/main.html',
                controller: 'MainController',
                controllerAs: 'vm',
                abstract: true
            })
            .state('home.controls', {
                url: '/controls',
                templateUrl: 'static/js/views/controls.html',
                data: {
                    title: 'Controls'
                }
            })
            .state('home.dashboard', {
                url: '/dashboard',
                templateUrl: 'static/js/views/dashboard.html',
                data: {
                    title: 'Dashboard'
                }
            })
            .state('home.viewer', {
                url: '/viewer',

                templateUrl: '/static/js/views/viewer.html',
                data: {
                    title: 'Viewer'
                }
            })
            .state('home.docs', {
                url: '/docs',

                templateUrl: '/static/js/views/docs.html',
                data: {
                    title: 'API Docs'
                }
            })

        $urlRouterProvider.otherwise('/controls');

        $mdThemingProvider
            .theme('default')
            .primaryPalette('grey', {
                'default': '600'
            })
            .accentPalette('teal', {
                'default': '500'
            })
            .warnPalette('defaultPrimary');

        $mdThemingProvider.theme('dark', 'default')
            .primaryPalette('defaultPrimary')
            .dark();

        $mdThemingProvider.theme('grey', 'default')
            .primaryPalette('grey');

        $mdThemingProvider.theme('custom', 'default')
            .primaryPalette('defaultPrimary', {
                'hue-1': '50'
            });

        $mdThemingProvider.definePalette('defaultPrimary', {
            '50': '#FFFFFF',
            '100': 'rgb(255, 198, 197)',
            '200': '#E75753',
            '300': '#E75753',
            '400': '#E75753',
            '500': '#E75753',
            '600': '#E75753',
            '700': '#E75753',
            '800': '#E75753',
            '900': '#E75753',
            'A100': '#E75753',
            'A200': '#E75753',
            'A400': '#E75753',
            'A700': '#E75753'
        });


    });