'use strict';
var angular = require('../../node_modules/@bower_components/angular')
angular
    .module('app')
    .controller('CollectorController', [
        '$scope',
        'statsService',
        CollectorController
    ]);

function CollectorController($scope,statsService) {
    var vm = this;
    


    $scope.collector_fps = 0;
    statsService.get_data(function(response) {
        var temp_j = (response.data).replace(/'/g, '"');
        $scope.stats_data = JSON.parse(temp_j);
        //console.log($scope.stats_data,'out');
        $scope.selected_source = statsService.get_selected_source()
        $scope.selected_pipeline = statsService.get_selected_pipeline()
        if ($scope.selected_source && $scope.selected_pipeline) {
            var collector_data = $scope.stats_data[$scope.selected_source].pipelines[$scope.selected_pipeline].collector
            if (collector_data) {
                $scope.collector_fps = collector_data['fps'];
            }
            $scope.$apply();

        }
        
    });

}






