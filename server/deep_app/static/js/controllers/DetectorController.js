'use strict';
var angular = require('../../node_modules/@bower_components/angular')
angular
    .module('app')
    .controller('DetectorController', [
        '$scope',
        'statsService',
        DetectorController
    ]);

function DetectorController($scope,statsService) {
    var vm = this;

    $scope.chart_data = [];
    $scope.detector_total = 0;
    $scope.detector_fps = 0;
    $scope.people = 0;
    statsService.get_data(function(response) {
        var temp_j = (response.data).replace(/'/g, '"');
        $scope.stats_data = JSON.parse(temp_j);
        //console.log($scope.stats_data,'out');
        $scope.chart_data = [];
        var detector_data = $scope.stats_data.FaceProvider;
        $scope.detector_fps = detector_data['fps'];
        $scope.detector_total = detector_data['received_frames'];
        $scope.people = detector_data['stat_people'];
        
        $scope.chart_data.push({key: 'elaborated frames', y: detector_data['elaborated_frames']});
        $scope.chart_data.push({key: 'skipped frames', y: detector_data['skipped_frames']});
        $scope.$apply();
    });

   
    vm.chartOptions = {
        chart: {
            type: 'pieChart',
            height: 210,
            donut: true,
            x: function (d) { return d.key; },
            y: function (d) { return d.y; },
            valueFormat: (d3.format(".0f")),
            color: ['rgb(0, 150, 136)', '#E75753'],
            showLabels: false,
            showLegend: false,
            margin: { top: -10 }
        }
    };


}

