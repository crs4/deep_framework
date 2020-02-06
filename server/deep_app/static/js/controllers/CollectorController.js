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
        
        var collector_data = $scope.stats_data.FaceCollector;
        if (collector_data) {
            $scope.collector_fps = collector_data['fps'];
        }
        $scope.$apply();
    });

}






