'use strict';
var angular = require('../../node_modules/@bower_components/angular')
var n= 0;

var colors =  [];
angular
    .module('app')
    .controller('AlgorithmController', [
        '$scope',
        '$compile',
        '$mdDialog',
        'algService',
        'statsService',
        AlgorithmController
    ]);
function start() {
    setInterval(increase, 1000);
    
}

function increase() {
    n++;
}

function random_rgb(){
    return 'rgb(' + (Math.floor(Math.random() * 256)) + ',' + (Math.floor(Math.random() * 256)) + ',' + (Math.floor(Math.random() * 256)) + ')';
}

  


function AlgorithmController($scope,$compile,$mdDialog,algService,statsService) {
    
    
    setTimeout(start, 1000);
    


    var chartOptions = {
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

    $scope.chartOptionsPerf = {
        chart: {
            type: 'stackedAreaChart',
            height: 350,
            margin: { left: +30, right: -15 },
            x: function (d) { return d[0] },
            y: function (d) { return d[1] },
            showLabels: true,
            showLegend: true,
            title: 'performance',
            duration: 0,
            showYAxis: true,
            showXAxis: true,
            
            tooltip: { contentGenerator: function (d) { return '<div class="custom-tooltip">' + d.point.y + ' fps</div>' + '<div class="custom-tooltip">' + d.series[0].key + '</div>' } },
            showControls: true
        }
    };

    
    var custom_scopes = {}
    var descriptors = new Set();
    var performance_dicts = {}
    function set_algs(algs_data) {
        if (algs_data == undefined) return
        Object.keys(algs_data).forEach((alg_name) => {
            if (!descriptors.has(alg_name)) {
                descriptors.add(alg_name)
                if (colors.length != descriptors.size) {
                    colors.push(random_rgb());
                }
                var performaces = {};
                var new_scope = $scope.$new(true);
                custom_scopes[alg_name] = new_scope;
                $('#alg_div').append($compile("<panel-widget flex title=" + alg_name + " template='static/js/views/partials/algorithm.html' class='fixed-height-widget'></panel-widget>")(new_scope));
                performance = { "key": alg_name, "values": [] };
                performance_dicts[alg_name] = performance
            }

        })
    }
    
    let selected_source = undefined
    let selected_pipeline = undefined
    $scope.performance_list = [];
    statsService.get_data(function(response) {

        var temp_j = (response.data).replace(/'/g, '"');
        var stats_data = JSON.parse(temp_j);
        let update_algs = false
        if (statsService.get_selected_source() != selected_source) {
            update_algs = true
            selected_source = statsService.get_selected_source()
        }
        if (selected_source == undefined) return
        if (statsService.get_selected_pipeline() != selected_pipeline) {
            update_algs = true
            selected_pipeline = statsService.get_selected_pipeline()
        }
        if (selected_pipeline == undefined) return
        var algs_data = stats_data[selected_source].pipelines[selected_pipeline].descriptors
        if (algs_data == undefined) {
            update_algs = true
        }
        if (update_algs) {
            for (let sc in custom_scopes) {
                custom_scopes[sc].$destroy()
            }
            custom_scopes = {}
            performance_dicts = {}
            $('#alg_div').empty()
            descriptors.clear()
            $scope.performance_list = [];
        }
        set_algs(algs_data)
        var i = 0;
        angular.forEach(algs_data, function(value, key) {
            var alg_scope = custom_scopes[key];
            //console.log(alg_scope.total);
            //console.log(alg_scope.fps);
            if (!alg_scope) return
            alg_scope.chart_data = [];
            alg_scope.chart_options = chartOptions;
            alg_scope.total = value['received_frames'];
            alg_scope.fps = value['fps'];
            alg_scope.title = key;
            alg_scope.options = chartOptions;
            alg_scope.chart_data.push({key: 'elaborated frames', y: value['elaborated_frames']});
            alg_scope.chart_data.push({key: 'skipped frames', y: value['skipped_frames']});
            alg_scope.$apply();
            if(performance_dicts[key]["values"].length > 50){
                performance_dicts[key]["values"].shift();
            }
            performance_dicts[key]["values"].push([n,alg_scope.fps]);
            performance_dicts[key]["color"] = colors[i];
            $scope.performance_list = Object.values(performance_dicts);
            i++;
        });
        $scope.$apply();

        

    });
    


}
