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
    $scope.streams = []
    dataService.getStreams().then((streams) => {
        $scope.streams = streams.map((s) => {
            return {
                id: s.id,
                type: s.type,
                active: false,
                busy: true,
                showData: false,
                connected: false
            }
        })
    })
    $scope.online = false
    $scope.status = 'offline'
    function update() {
        $scope.online = dataService.isOnline()
        $scope.status = dataService.getStatus()
        if ($scope.online) {
            dataService.getActiveStreams()
                .then((activeStreams) => {
                    $scope.streams.forEach((stream, index, streams) => {
                        streams[index].active = false
                        streams[index].busy = true
                        streams[index].connected = false
                        activeStreams.forEach((s) => {
                            if (stream.id == s.id) {
                                streams[index].active = true
                                streams[index].busy = s.busy
                                if ($scope.status == 'connected' && dataService.getRemotePeer().id == stream.id){
                                    streams[index].connected = true
                                }
                            }
                        })
                    })
                })
        }
        // $scope.$apply()
    }
    update()
    if (!$scope.online) {
        dataService.connect()
        .then(() => {
            $scope.online = true
            
        })
        .catch((e) => alert(JSON.stringify(e)))
    }
    setInterval(update, 1000)

    $scope.lastData = {}
    $scope.showLocalVideo = false
    $scope.showRemoteVideo = false
    $scope.showingData = false

    $scope.disconnect = function () {
        dataService.disconnect(() => {
            $scope.online = false
            $scope.$apply()
        })
    }

    // const ringtone = angular.element('//ringtone')//$document.getElementById('//ringtone');
    let video = ($('#video'))[0]
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
        video.srcObject = dataService.getRemoteStream()
        deepConnection.onAny(handleConnectionChange)
        deepConnection.on('data', handleIncomingData)
    }

    $scope.$on('$destroy', () => {
        if ($scope.status === 'connected') {
            deepConnection.offAny(handleConnectionChange)
            deepConnection.removeListener('data', handleIncomingData)
        }
        if ($scope.showingData) dataService.hideDataStream()
    })

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

    $scope.startStream = function (streamId) {
        dataService.startStream(streamId)
            .then(() => {
                console.log('Stream started')
            })
            .catch(alert)
    }

    $scope.stopStream = function (streamId) {
        dataService.stopStream(streamId)
            .then(() => {
                console.log('Stream stoped')
            })
            .catch(alert)
    }


    $scope.stopPeerConnection = function (stream) {
        dataService.stopPeerConnection()
            .then(() => stream.connected = false)
    }

    $scope.startPeerConnection = function (stream) {
        dataService.startPeerConnection(stream)
            .then((remoteStream) => {
                video.srcObject = remoteStream
                deepConnection = dataService.getConnection()
                deepConnection.onAny(handleConnectionChange)
                deepConnection.on('data', handleIncomingData)
                deepConnection.once('disconnect', () => {
                    video.pause()
                    video.srcObject = undefined
                })
                stream.connected = true
            })
            .catch((error) => alert(JSON.stringify(error)))
    }

    $scope.dataMessage = {}
    $scope.showDataStream = function (stream) {
        dataService.hideDataStream()
        $scope.streams.forEach((stream) => {
            stream.showData = false
        })
        dataService.showDataStream(stream.id, (event) => {
            $scope.dataMessage = JSON.parse(event.data)
        })
        stream.showData = true
        $scope.showingData = true
    }

    $scope.hideDataStream = function(stream) {
        dataService.hideDataStream()
        stream.showData = false
        $scope.showingData = false
    }


    let videoEvents = ['play', 'pause', 'stalled', 'ended', 'waiting', 'canplay', 'canplaythrough', 'connected', 'suspend', 'loadeddata']
    videoEvents.forEach((event) => {
        video.addEventListener(event, () => {
            console.log('*** Remote video event: ' + event)
            if (event === 'canplaythrough') playVideo(video)
            if (event === 'pause') video.controls = true

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
