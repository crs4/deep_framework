'use strict';
var angular = require('../../node_modules/@bower_components/angular')
angular.module('app').controller('StatsController', [
        '$scope',
        StatsController
    ]);

function StatsController($scope) {
    var vm = this;
    vm.detector_data = [];
    vm.detector_fps = null;
    vm.detector_total = null;

    var source = new EventSource('/stats_stream');
    source.onmessage = function(e) {
        vm.detector_data = [];
        var temp_j = (e.data).replace(/'/g, '"');
        data = JSON.parse(temp_j);
        temp_detector_data = data.FrameProvider;

        vm.detector_fps = temp_detector_data['fps'];
        vm.detector_total = temp_detector_data['received_frames'];
        
        vm.detector_data.push({key: 'elaborated frames', y: temp_detector_data['elaborated_frames']});
        vm.detector_data.push({key: 'skipped frames', y: temp_detector_data['skipped_frames']});
        
        $scope.$apply();

        
    };

    source.addEventListener('error', function(e) {
        console.log(e);
        if (e.readyState == EventSource.CLOSED) {
        // Connection was closed.
        }
    }, false);

    // TODO: move data to the service
    vm.visitorsChartData = [ {key: 'Mobile', y: 5264}, { key: 'Desktop', y: 3872} ];

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

