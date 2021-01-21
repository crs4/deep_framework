'use strict';
console.log('VIEWER CONTROLLER LOADING...')

var angular = require('../../node_modules/@bower_components/angular')
angular
    .module('app')
    .controller('ViewerController', [
        '$scope', '$timeout',
        'dataService',
        ViewerController
    ]);

function ViewerController($scope, $timeout, dataService) {
    let deepConnection = dataService.getConnection()
    $scope.remotePeerType = dataService.getRemotePeerType()
    $scope.deepVideoSource = dataService.getDeepVideoSource()
    $scope.status = dataService.getStatus()
    $scope.faces = []
    $scope.showDetails = false
    
    let video = ($('#video'))[0]
    let canvas = $('#canvas')[0] //$document.getElementById('canvas');
    $scope.demoVideoCanvas = $scope.remotePeerType == 'stream_manager' ? new EnhancedFacesVideoCanvas(video, canvas) : new EnhancedVideoCanvas(video, canvas)
    
    function handleConnectionChange() {
        $timeout(() => {
            $scope.status = dataService.getStatus()
            $scope.$apply()
        }, 0.5)
    }

    function handleIncomingData(data) {
        if (data.type == 'data') {
            $scope.demoVideoCanvas.setData(data)
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
        window.cancelAnimationFrame($scope.requestAnimationId)
        console.log('*** Video animation ends ***')
    })

    function refreshVideoCanvas() {
        // request new frame
        $scope.requestAnimationId = window.requestAnimationFrame(refreshVideoCanvas)
        $scope.demoVideoCanvas.refresh()
    };
    
    video.addEventListener('play', function () {
        console.log('*** Video animation starts ***')
        refreshVideoCanvas();
    }, false);

}

class EnhancedVideoCanvas {
    constructor(videoElement, canvasElement) {
        this.video = videoElement
        this.canvas = canvasElement
        this.context = this.canvas.getContext('2d')
    }

    setData(data) {
        if (data.objects) this.objects = data.objects
        if (data.frame_shape) {
            this.frameWidth = data.frame_shape[1]
            this.frameHeight = data.frame_shape[0]
        }
    }

    refresh() {
        let vw = this.video.videoWidth
        let vh = this.video.videoHeight
        this.aspectRatio = vw / vh
        this.canvas.width = this.canvas.parentElement.offsetWidth
        this.canvas.height = this.canvas.width / this.aspectRatio
        this.context.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height)
    }

    getXScaleFactor() {
        return this.canvas.width / this.video.videoWidth
    }

    getYScaleFactor() {
        return this.canvas.height / this.video.videoHeight
    }
}

class EnhancedFacesVideoCanvas extends EnhancedVideoCanvas{
    constructor(...args) {
        super(...args)
        this.facesData = {}
        this.boxColors = ['yellow', 'red', 'blue', 'lime', 'orange', 'magenta', 'cyan', 'gold', 'purple', 'green']
        //this.boxColors = [];
        
        this.availableBoxColors = this.boxColors.map(c => c)
        this.faceColorMap = new Map()
    }

    setData(data) {
        super.setData(data)
        this.facesData = {}
        if (!this.objects.length) return
        const faces = this.objects
        faces.forEach((face) => {
            let faceData = {
                pid: face.pid,
                bbox: face.rect,
                name: !face.face_recognition || face.face_recognition == 'Unknown' ?
                    `${face.class} ${face.pid.slice(-4)}` : face.face_recognition,
                pitch: face.pitch,
                yaw: face.yaw,
                gender: face.gender ? face.gender : '-',
                age: face.age ? face.age.slice(1, 7).replace(',', () => ' -') : '-',
                emotions: face.emotion ? face.emotion.map(e => {
                    return {
                        label: e[0],
                        emoticon: e[0] + '.png',
                        emoticonSize: e[1] < 0.1 ? 0 : e[1] * 32 + 16
                    }
                }) : [],
                glasses: face.glasses ? face.glasses.slice(2, -1) : ''
            }
            faceData.color = this.faceColorMap.get(face.class)
            if (!faceData.color) {
                faceData.color = this.availableBoxColors.shift()
            }
            if (!faceData.color) {
                faceData.color = 'black'
            }
            this.faceColorMap.set(face.class, faceData.color)
            this.facesData[face.pid] = faceData
        })
        if (Object.keys(this.facesData).length < this.faceColorMap.size) {
            this.faceColorMap.forEach((value, key, map) => {
                if (!this.facesData.hasOwnProperty(key) && value != 'black') {
                    map.delete(key)
                    this.availableBoxColors.push(value)
                }
            })
        }
    }

    refresh() {
        super.refresh()
        for (let face in this.facesData) {
            let faceData = this.facesData[face]
            if (!faceData.bbox) return
            const xScaleFactor = this.frameWidth ? this.canvas.width / frameWidth : this.getXScaleFactor()
            const yScaleFactor = this.frameHeight ? this.canvas.height / frameHeight : this.getYScaleFactor()
            var x = faceData.bbox.x_topleft * xScaleFactor
            var y = faceData.bbox.y_topleft * yScaleFactor
            var w = (faceData.bbox.x_bottomright - faceData.bbox.x_topleft) * xScaleFactor
            var h = (faceData.bbox.y_bottomright - faceData.bbox.y_topleft) * yScaleFactor
            this.context.beginPath()
            this.context.rect(x, y, w, h)
            this.context.lineWidth = 5
            this.context.strokeStyle = faceData.color
            this.context.stroke()
            if (faceData.pitch) {
                const pitchScaling = h / 30
                let px = x
                let py = y + h / 2 - faceData.pitch * pitchScaling
                let pw = 10
                let ph = faceData.pitch * pitchScaling
                this.context.beginPath()
                this.context.rect(px, py, pw, ph)
                this.context.fillStyle = '#8ED6FF'
                this.context.fill()
                this.context.lineWidth = 1
                this.context.strokeStyle = faceData.color
                this.context.stroke()
            }
            if (faceData.yaw) {
                const yawScaling = w / 120
                let yx = x + w / 2 - faceData.yaw * yawScaling
                let yy = y
                let yw = faceData.yaw * yawScaling
                let yh = 10
                this.context.beginPath()
                this.context.rect(yx, yy, yw, yh)
                this.context.fillStyle = '#8ED6FF'
                this.context.fill()
                this.context.lineWidth = 1
                this.context.strokeStyle = faceData.color
                this.context.stroke()
            }
            this.context.font = "20px Arial"
            this.context.fillStyle = faceData.color
            this.context.fillText(faceData.name, faceData.bbox.x_topleft * xScaleFactor + 5, faceData.bbox.y_bottomright * yScaleFactor - 10)
        }
    }
}