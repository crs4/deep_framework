'use strict';
var angular = require('../../node_modules/@bower_components/angular')
angular
    .module('app')
    .controller('StreamStatsController', [
        '$scope', '$timeout',
        'statsService',
        StreamStatsController
    ]);


function StreamStatsController($scope, $timeout, statsService) {
    $scope.fps = 0
    $scope.stream_data = {}
    $scope.selected_source = undefined
    $scope.messages = 0
    statsService.get_data(function (response) {
        var temp_j = (response.data).replace(/'/g, '"');
        $scope.stats_data = JSON.parse(temp_j)
        //console.log($scope.stats_data,'out');
        $scope.sources = Object.keys($scope.stats_data)
        $scope.selected_source = statsService.get_selected_source()
        
        if ($scope.selected_source) {
            $scope.stream_data = $scope.stats_data[$scope.selected_source].stream_manager
            $scope.fps = $scope.stream_data.processing_period > 0 ? 1 / $scope.stream_data.processing_period : 0
        }

        $scope.messages += 1
        // $scope.$apply()
    })

   

}
