'use strict';
var angular = require('../../node_modules/@bower_components/angular')
angular
    .module('app')
    .controller('CaptureController', [
        '$scope',
        'statsService',
        CaptureController
    ]);

function CaptureController($scope,statsService) {
    var vm = this;
    


    $scope.capture_total = 0;
    $scope.capture_fps = 0;
    statsService.get_data(function(response) {
        var temp_j = (response.data).replace(/'/g, '"');
        $scope.stats_data = JSON.parse(temp_j);
        //console.log($scope.stats_data,'out');
        var capture_data = $scope.stats_data.VideoCapture;
        if (capture_data) {
            $scope.capture_fps = capture_data['fps'];
            $scope.capture_total = capture_data['elaborated_frames'];
            $scope.start_time = capture_data['start_time'];

        }
        
        $scope.$apply();
    });




}









