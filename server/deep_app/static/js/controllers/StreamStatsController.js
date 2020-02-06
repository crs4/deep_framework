'use strict';
var angular = require('../../node_modules/@bower_components/angular')
angular
    .module('app')
    .controller('StreamStatsController', [
        '$scope', '$timeout',
        'dataService',
        StreamStatsController
    ]);


function StreamStatsController($scope, $timeout, dataService) {
    let deepConnection = dataService.getConnection()
    $scope.remotePeer = dataService.getRemotePeer()
    $scope.remotePeerType = dataService.getRemotePeerType()
    $scope.deepVideoSource = dataService.getDeepVideoSource()
    $scope.online = dataService.isOnline()
    $scope.status = dataService.getStatus()
    

    let frame_rates = []
    $scope.connectionData = {}

    function handleConnectionChange() {
        $timeout(() => {
            $scope.status = dataService.getStatus()
            // console.log('Status: ' + $scope.status)
            $scope.$apply()
        }, 0.1)
    }

    function handleIncomingData(data) {
        if (data.type == 'data') {
            // if (frame_rates.length >= 30) {
            //     frame_rates.shift()
            // }
            // frame_rates.push(data.current_frame_rate)
            // let mean_frame_rate = 0
            // frame_rates.forEach(r => mean_frame_rate += r)
            // mean_frame_rate /= frame_rates.length
            $scope.received_frames = data.received_frames
            $scope.generated_frames = data.generated_frames
            $scope.processed_frames = data.processed_frames
            $scope.deep_delay = data.deep_delay.toFixed(3)
            $scope.net_delay = (data.round_trip / 2).toFixed(3)
            $scope.resolution = `${data.last_frame_shape[1]} x ${data.last_frame_shape[0]}`
            $scope.processing_period = data.processing_period.toFixed(3)
            $scope.fps = (1 / data.processing_period).toFixed(3)
            //console.log($scope.connectionData)
        }
    }

    if ($scope.status === 'connected') {
        deepConnection.onAny(handleConnectionChange)
        deepConnection.on('data', handleIncomingData)
    }

    $scope.$on('$destroy', () => {
        if ($scope.status === 'connected') {
            deepConnection.offAny(handleConnectionChange)
            deepConnection.removeListener('data', handleIncomingData)
        }
    })

   

}
