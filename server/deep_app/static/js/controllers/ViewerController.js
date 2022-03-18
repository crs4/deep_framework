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
    $scope.status = dataService.getStatus()
    $scope.faces = []
    $scope.showDetails = false
    
    let video = ($('#video'))[0]
    let canvas = $('#canvas')[0] //$document.getElementById('canvas');
    let hidden_canvas = $('#hidden_canvas')[0]
    $scope.faceRenderer = new EnhancedFacesVideoCanvas(video, canvas)
    $scope.objectRenderer = new EnhancedObjectsVideoCanvas(video, canvas, hidden_canvas)
    
    function handleConnectionChange() {
        $timeout(() => {
            $scope.status = dataService.getStatus()
            $scope.$apply()
        }, 0.5)
    }

    function handleIncomingData(data) {
        if (data.type != 'data') return
        $scope.objectRenderer.setData(data)
        if (data.detector_category == 'face') {
            $scope.faceRenderer.setData(data)
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
        $scope.objectRenderer.refresh()
        $scope.faceRenderer.refresh()
    };
    
    video.addEventListener('play', function () {
        console.log('*** Video animation starts ***')
        refreshVideoCanvas();
    }, false);

    $scope.selectTarget = function (event) { 
        $scope.objectRenderer.setTargetObject(event.offsetX, event.offsetY)
        setTimeout(() => {
            // let text
            // if ($scope.objectRenderer.targetObject.target_bbox != undefined) {
            //     text = "Confirm target in RED!\nEither OK or Cancel."
            // }  else {
            //     text = "Confirm NO target!\nEither OK or Cancel."
            // }
            // if (confirm(text) == true) {
            //     console.log("You pressed OK!")
            //     let message = { 
            //         type: 'metadata', 
            //         metadata: $scope.objectRenderer.targetObject
            //     }
            //     deepConnection.send(message)
            //     $scope.objectRenderer.targetObject = {}
            // } else {
            //     console.log("You canceled!")
            // }
            let message = {
                type: 'metadata',
                metadata: $scope.objectRenderer.targetObject
            }
            deepConnection.send(message)
            $scope.objectRenderer.targetObject = {}
            console.log('metadata sent!')
        }, 1)
    };
}

class EnhancedVideoCanvas {
    constructor(videoElement, canvasElement) {
        this.video = videoElement
        this.canvas = canvasElement
        this.context = this.canvas.getContext('2d')
        this.frozen = false
    }

    setData(data) {
        if (data.frame_shape) {
            this.frameWidth = data.frame_shape[1]
            this.frameHeight = data.frame_shape[0]
        }
    }

    refresh() {
        if (this.frozen) return
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

    freeze() {
        this.frozen = true
    }

    unfreeze() {
        this.frozen = false
    }
}

class EnhancedObjectsVideoCanvas extends EnhancedVideoCanvas{
    constructor(videoElement, canvasElement, hidden_canvas) {
        super(videoElement, canvasElement)
        this.objectsData = {}
        this.boxColors = ['yellow', 'red', 'blue', 'lime', 'orange', 'magenta', 'cyan', 'gold', 'purple', 'green']
        //this.boxColors = [];
        this.objects = {}
        this.availableBoxColors = this.boxColors.map(c => c)
        this.objColorMap = new Map()
        this.target = {x: 0, y: 0}
        this.targetObject = {}
        this.hidden_canvas = hidden_canvas
    }

    setData(data) {
        if (this.frozen) return
        super.setData(data)
        this.objects[data.detector_category] = []
        for (const obj of data.objects) {
            let objectData = {
                pid: obj.pid,
                bbox: obj.rect
            }
            const color_class = data.detector_category + obj.class
            objectData.color = this.objColorMap.get(color_class)
            if (!objectData.color) {
                objectData.color = this.availableBoxColors.shift()
            }
            if (!objectData.color) {
                objectData.color = 'black'
            }
            this.objColorMap.set(color_class, objectData.color)
            this.objects[data.detector_category].push(objectData)
        }
        // Reuse colors when assigned to object type that disappear
        // if (Object.keys(this.objects).length < this.objColorMap.size) {
        //     this.objColorMap.forEach((value, key, map) => {
        //         if (!this.objectsData.hasOwnProperty(key) && value != 'black') {
        //             map.delete(key)
        //             this.availableBoxColors.push(value)
        //         }
        //     })
        // }
    }

    refresh() {
        super.refresh()
        for (const det_cat in this.objects) {
            for (const objectData of this.objects[det_cat]) {
                if (!objectData.bbox) return
                const xScaleFactor = this.frameWidth ? this.canvas.width / frameWidth : this.getXScaleFactor()
                const yScaleFactor = this.frameHeight ? this.canvas.height / frameHeight : this.getYScaleFactor()
                var x = objectData.bbox.x_topleft * xScaleFactor
                var y = objectData.bbox.y_topleft * yScaleFactor
                var w = (objectData.bbox.x_bottomright - objectData.bbox.x_topleft) * xScaleFactor
                var h = (objectData.bbox.y_bottomright - objectData.bbox.y_topleft) * yScaleFactor
                if (this.frozen) {
                    if (this.target.x > x && this.target.x < x + w && this.target.y > y && this.target.y < y + h) {
                        // objectData.color = 'red'
                        // var imgData = this.context.getImageData(x, y, w, h)
                        // var ctx = this.hidden_canvas.getContext('2d')
                        // var scale = this.hidden_canvas.height / h
                        // this.hidden_canvas.width = w * scale
                        // ctx.scale(scale, scale)
                        // this.putImageData(ctx, imgData, 0, 0)
                        // var targetImg = this.hidden_canvas.toDataURL()//this.context.getImageData(x, y, w, h)
                        this.targetObject = {
                            target_bbox: objectData.bbox,
                            //target_image: targetImg
                        }
                    }
                }
                this.context.beginPath()
                this.context.rect(x, y, w, h)
                this.context.lineWidth = 5
                this.context.strokeStyle = objectData.color
                this.context.stroke()
        
                // this.context.font = "20px Arial"
                // this.context.fillStyle = objectData.color
                // this.context.fillText('ciao', objectData.bbox.x_topleft * xScaleFactor + 5, objectData.bbox.y_bottomright * yScaleFactor - 10)

            }
        }
    }

    putImageData(ctx, imageData, dx, dy,
        dirtyX, dirtyY, dirtyWidth, dirtyHeight) {
        var data = imageData.data;
        var height = imageData.height;
        var width = imageData.width;
        dirtyX = dirtyX || 0;
        dirtyY = dirtyY || 0;
        dirtyWidth = dirtyWidth !== undefined ? dirtyWidth : width;
        dirtyHeight = dirtyHeight !== undefined ? dirtyHeight : height;
        var limitBottom = dirtyY + dirtyHeight;
        var limitRight = dirtyX + dirtyWidth;
        for (var y = dirtyY; y < limitBottom; y++) {
            for (var x = dirtyX; x < limitRight; x++) {
                var pos = y * width + x;
                ctx.fillStyle = 'rgba(' + data[pos * 4 + 0]
                    + ',' + data[pos * 4 + 1]
                    + ',' + data[pos * 4 + 2]
                    + ',' + (data[pos * 4 + 3] / 255) + ')';
                ctx.fillRect(x + dx, y + dy, 1, 1);
            }
        }
    }

    setTargetObject(x, y) {
        super.refresh()
        this.freeze()
        console.log("frozen!")
        // this.context.font = "20px Arial"
        // this.context.fillStyle = "red"
        // this.context.fillText("target", x, y)
        this.target = {x, y}
        this.refresh()
        
        this.unfreeze()
    }
}

class EnhancedFacesVideoCanvas extends EnhancedVideoCanvas {
    constructor(...args) {
        super(...args)
        this.facesData = {}
        this.haveData = false
    }

    setData(data) {
        super.setData(data)
        this.facesData = {}
        if (!data.objects.length) {
            this.haveData = false
            return
        }
        const faces = data.objects
        faces.forEach((face) => {
            let faceData = {
                pid: face.pid,
                bbox: face.rect,
                name: !face.face_recognition || face.face_recognition.value == 'Unknown' ?
                    `${face.class} ${face.pid.slice(-4)}` : face.face_recognition.value,
                pitch: face.pitch ? face.pitch.value : undefined,
                yaw: face.yaw ? face.yaw.value : undefined,
                gender: face.gender ? face.gender.value : '-',
                age: face.age ? face.age.value.slice(1, 7).replace(',', () => ' -') : '-',
                emotions: face.emotion ? face.emotion.value.map(e => {
                    return {
                        label: e[0],
                        emoticon: e[0] + '.png',
                        emoticonSize: e[1] < 0.1 ? 0 : e[1] * 32 + 16
                    }
                }) : [],
                glasses: face.glasses ? face.glasses.value.slice(2, -1) : ''
            }
            faceData.color = 'black'
            this.facesData[face.pid] = faceData
        })
        this.haveData = true
    }

    refresh() {
        // super.refresh()
        for (let face in this.facesData) {
            let faceData = this.facesData[face]
            if (!faceData.bbox) return
            const xScaleFactor = this.frameWidth ? this.canvas.width / frameWidth : this.getXScaleFactor()
            const yScaleFactor = this.frameHeight ? this.canvas.height / frameHeight : this.getYScaleFactor()
            var x = faceData.bbox.x_topleft * xScaleFactor
            var y = faceData.bbox.y_topleft * yScaleFactor
            var w = (faceData.bbox.x_bottomright - faceData.bbox.x_topleft) * xScaleFactor
            var h = (faceData.bbox.y_bottomright - faceData.bbox.y_topleft) * yScaleFactor
            // this.context.beginPath()
            // this.context.rect(x, y, w, h)
            // this.context.lineWidth = 5
            // this.context.strokeStyle = faceData.color
            // this.context.stroke()
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