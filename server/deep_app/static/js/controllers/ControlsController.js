'use strict';
var angular = require('../../node_modules/@bower_components/angular')
angular
    .module('app')
    .controller('ControlsController', [
        '$scope', '$timeout',
        'dataService',
        ControlsController
    ]);



function ControlsController($scope, $timeout, dataService) {
    let deepConnection = dataService.getConnection()
    $scope.servers = dataService.getServers()
    $scope.cameras = dataService.getCameras()
    $scope.myPeerId = dataService.getMyPeerId()
    $scope.remotePeer = dataService.getRemotePeer()
    $scope.remotePeerType = dataService.getRemotePeerType()
    $scope.deepVideoSource = dataService.getDeepVideoSource()
    $scope.online = dataService.isOnline()
    $scope.status = dataService.getStatus()
    $scope.lastData = {}
    $scope.showLocalVideo = false
    $scope.showRemoteVideo = false
    $scope.showData = false

    $scope.$watch('deepVideoSource', (newValue, oldValue) => {
        if ($scope.status == 'connected') {
            console.log('** DeepVideoSource: ' + newValue)
            dataService.setDeepVideoSource(newValue)
        }
    })

    $scope.$watch('remotePeerType', (newValue, oldValue) => {
        dataService.setRemotePeerType(newValue)
    })

    $scope.$watch('remotePeer', (newValue, oldValue) => {
        dataService.setRemotePeer(newValue)
    })

    $scope.disconnect = function () {
        dataService.disconnect(() => {
            $scope.online = false
            $scope.$apply()
        })
    }

    // const ringtone = angular.element('//ringtone')//$document.getElementById('//ringtone');
    let video = ($('#video'))[0]
    let localVideo = ($('#local_video'))[0]
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
            if (frame_rates.length >= 30) {
                frame_rates.shift()
            }
            frame_rates.push(data.current_frame_rate)
            let mean_frame_rate = 0
            frame_rates.forEach(r => mean_frame_rate += r)
            mean_frame_rate /= frame_rates.length
            $scope.connectionData = {
                // deepDelay: data.collector_time - data.vc_time,
                // serverDelay: data.rec_time - data.collector_time,
                // browserTime: Date.now() / 1000,
                // totalDelay: data.vc_time - Date.now() / 1000,
                // current_video_resolution: data.current_video_resolution,
                // mean_frame_rate: mean_frame_rate
            }
            $scope.lastData = data
            //console.log($scope.connectionData)
        }
    }

    if ($scope.status === 'connected') {
        localVideo.srcObject = dataService.getLocalStream()
        video.srcObject = dataService.getRemoteStream()
        deepConnection.onAny(handleConnectionChange)
        deepConnection.on('data', handleIncomingData)
    }

    $scope.$on('$destroy', () => {
        if ($scope.status === 'connected') {
            deepConnection.offAny(handleConnectionChange)
            deepConnection.removeListener('data', handleIncomingData)
        }
    })

    $scope.connect = function () {
        if (dataService.isOnline()) {
            dataService.disconnect(() => {
                $scope.connect();
            })
        }
        dataService.connect((error, localStream) => {
            if (error) {
                alert(JSON.stringify(error))
            }
            console.log('connected')
            localVideo.srcObject = localStream


            deepConnection = dataService.getConnection()
            $scope.servers = dataService.getServers()
            $scope.cameras = dataService.getCameras()
            $scope.online = dataService.isOnline()

            $scope.status = dataService.getStatus()
            $scope.$apply()

            deepConnection.onAny(handleConnectionChange)
            deepConnection.on('data', handleIncomingData)
        })
    }

    $scope.startStreams = function() {
        dataService.startStreams()
        .then(()=>{
            console.log('Streams started')
        })
        .catch(alert)
    }

    $scope.stopStreams = function () {
        dataService.stopStreams()
            .then(() => {
                console.log('Streams stoped')
            })
            .catch(alert)
    }


    $scope.stop = function () {
        dataService.stop()
        $scope.deepVideoSource = dataService.getDeepVideoSource()
    };

    $scope.start = function () {
        if (!$scope.remotePeer) return alert('No server available');
        dataService.start((error, remoteStream) => {
            if (error) return alert(JSON.stringify(error))
            video.srcObject = remoteStream
            deepConnection.once('disconnect', () => {
                video.pause()
                video.srcObject = undefined
            })
        })
    };


    let videoEvents = ['play', 'pause', 'stalled', 'ended', 'waiting', 'canplay', 'canplaythrough', 'connected', 'suspend', 'loadeddata']
    videoEvents.forEach((event) => {
        video.addEventListener(event, () => {
            console.log('*** Remote video event: ' + event)
            if (event === 'canplaythrough') playVideo(video)
            if (event === 'pause') video.controls = true

        }, false)
        localVideo.addEventListener(event, () => {
            console.log('*** Local video event: ' + event)
            if (event === 'canplaythrough') playVideo(localVideo)
            if (event === 'pause') localVideo.controls = true
        }, false)
    })
    $scope.manualPlay = false
    $scope.goPlay = function () { }
    function playVideo(videoElem) {
        let startPlayPromise = videoElem.play();

        if (startPlayPromise !== undefined) {
            startPlayPromise.catch(error => {
                if (error.name === "NotAllowedError") {
                    console.log('activating controls..')
                    $scope.manualPlay = true
                    $scope.goPlay = function () {
                        videoElem.play().catch((error) => { alert(JSON.stringify(error)) });
                    };
                } else {
                    // Handle a load or playback error
                    console.error('Play error: ' + error)
                }
            }).then(() => {
                // Start whatever you need to do only after playback
                // has begun.
                videoElem.controls = false

            });
        }

    }

}
