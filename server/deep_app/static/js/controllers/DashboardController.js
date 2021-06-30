'use strict';
var angular = require('@bower_components/angular')
angular
    .module('app')
    .controller('DashboardController', [
        '$scope',
        'statsService',
        DashboardController
    ]);

function DashboardController($scope,statsService) {
    
    $scope.sources = statsService.get_sources()
    $scope.pipelines = statsService.get_pipelines()
    $scope.selected_source = statsService.get_selected_source()
    $scope.selected_pipeline = statsService.get_selected_pipeline()
    setTimeout(() =>  {
        $scope.sources = statsService.get_sources()
        $scope.pipelines = statsService.get_pipelines()
        $scope.selected_source = statsService.get_selected_source()
        $scope.selected_pipeline = statsService.get_selected_pipeline()
    }, 1000)
    $scope.messages = 0
    $scope.$watch('selected_source', function (newValue, oldValue) {
        statsService.set_selected_source(newValue)
        $scope.pipelines = statsService.get_pipelines()
        $scope.selected_pipeline = statsService.get_selected_pipeline()
        // if (newValue != oldValue) {
        // }
        // $scope.$apply()
    })
    $scope.$watch('selected_pipeline', function (newValue, oldValue) {
        statsService.set_selected_pipeline(newValue)
        // $scope.$apply()
    })
}






