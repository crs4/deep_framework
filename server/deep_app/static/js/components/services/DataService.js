'use strict';
var angular = require('../../../node_modules/@bower_components/angular')
angular.module('app')
  .service('dataService', ['$window', '$http',
    dataService
  ]);
console.log('Data Service')
const Hyperpeer = require('hyperpeer-js');
let supports = navigator.mediaDevices.getSupportedConstraints()
let constraints
if (!supports["width"] || !supports["height"] || !supports["frameRate"] || !supports["facingMode"]) {
  // We're missing needed properties, so handle that error.
  alert('Missing needed properties ')
  console.error('Missing needed properties:')
  console.error(supports)
  constraints = { video: { width: 640, height: 480 }, audio: false }
} else {
  constraints = {
    video: {
      width: { min: 640, ideal: 1280, max: 1920 },
      height: { min: 480, ideal: 720, max: 1080 },
      //aspectRatio: { ideal: 1.7777777778 },
      frameRate: { min: 5, ideal: 10, max: 15 },
      //facingMode: { exact: "user" },
    },
    audio: false
    // {
    //   sampleSize: 16,
    //   channelCount: 2,
    //   sampleRate: 41000
    // }
  }
}
/**
 *
 *
 * @returns
 */
function dataService($window, $http) {
  const hostname = location.hostname;
  console.log(hostname)
  const serverAddress = `wss://${hostname}:8000`; //156.148.132.107
  let hp = null;
  const userType = 'web_client'
  const username = 'webClient' + Date.now()
  let remoteStream = null
  let dataStreams = []
  let remotePeer = null
  return {
    getConnection: () => hp,
    getRemotePeer: () => remotePeer,
    getLocalStream: () => localStream,
    getRemoteStream: () => remoteStream,
    getStatus: () => hp ? hp.readyState : 'offline',
    isOnline: function () {
      if (hp) {
        if (hp.readyState != Hyperpeer.states.CLOSED) {
          return true
        }
      }
      return false
    },
    disconnect: function (callback) {
      if (hp) {
        hp.close()
        hp.once('close', () => {
          callback()
        })
      } else {
        callback()
      }
    },
    connect: function () {
      return new Promise((resolve, reject) => {
        let connected = false
        hp = new Hyperpeer(serverAddress, {
          id: username,
          type: userType,
          // stream: stream,
          // videoElement: video,
          datachannelOptions: {
            ordered: false,
            maxPacketLifeTime: 0,
            protocol: ''
          }
        });
  
        hp.onAny(function (event, value) {
          let payload = '.'
          if (value) {
            payload = ': ' + JSON.stringify(value)
          }
          // console.log('Hyperpeer event: ' + event + payload)
        });
        
        hp.on('error', (error) => {
          if (!connected) {
            return reject(error)
          }
          alert(JSON.stringify(error))
        })
  
        hp.once('online', () => {
          connected = true
          resolve()
        })
  
        hp.on('close', () => {
          setTimeout(() => {
            console.log('Connection ends')
            hp.removeAllListeners()
            hp = null
          }, 0.01)
        })
  
        hp.on('disconnect', () => {
          remotePeer = null
        })
  
        hp.on('data', (data) => {
          if (!data.type) {
            console.error('Missing type in data message');
            alert('Missing type in data message' + JSON.stringify(data))
          }
          if (data.type == 'data') {
            let acknowledge = { 
              type: 'acknowledge', 
              messages_received: 
              data.messages_sent, 
              browser_time: Date.now() / 1000, 
              rec_time: data.rec_time 
            }
            hp.send(acknowledge)
          } else if (data.type == 'error') {
            this.stop()
            alert('Deep error' + JSON.stringify(data))
          } else if (data.type == 'source-disconnected') {
            deepVideoSource = 'none'
            alert('Video source disconnected. Reason: ' + data.reason)
          }
          else {
            console.warn('Deep message' + JSON.stringify(data))
          }
        })

      })
    },
    startPeerConnection: function (peer) {
  
      hp.once('stream', (s) => {
        remoteStream = s
        console.log('remote stream: ' + s.id + '. Active: ' + s.active)
      })
      return new Promise((resolve, reject) => {
        if (!hp) return reject()
        if (peer.type == 'remote_client') {
          $window.navigator.mediaDevices.getUserMedia(constraints)//{ video: { width: 1280, height: 720, frameRate: 10 }, audio: true })
          .then((localStream) => {
            hp.stream = localStream
            hp.once('disconnect', () => {
              localStream.getTracks().forEach(track => track.stop())
            })
            resolve(hp.connectTo(peer.id))
          })
          .catch(reject)
        } else {
          resolve(hp.connectTo(peer.id))
        }
      })
      .then(() => {
        if (peer.type == 'remote_client'){
          hp.send({ type: 'metadata', metadata: { type: 'browser_video' } })
        }
        remotePeer = peer
        return remoteStream
      })
    },
    stopPeerConnection: function() {
      return hp.disconnect()
    },
    startStreams: () => {
      return $http.post("/api/start", null)
    },
    stopStreams: () => {
      return $http.post("/api/stop", null)
    },
    getStreams: () => {
      return $http.get("/api/sources").then(function (response) {
        return response.data
      })
    },
    getActiveStreams: () => {
      return hp.getPeers()
    },
    startStream: (streamId) => {
      return $http.post("/api/stream_"+streamId+"/start", null)
    },
    stopStream: (streamId) => {
      return $http.post("/api/stream_" + streamId + "/stop", null)
    },
    showDataStream: (stream, callback) => {
      dataStreams.forEach((ds) => ds.close())
      dataStreams = stream.detector.map((det) => {
        let dataStream = new EventSource('/api/stream_' + stream.id + '/' + det)
        dataStream.addEventListener('message', callback.bind(null, det), false)
        return dataStream
      })
      
    },
    hideDataStream: () => {
      dataStreams.forEach((ds) => ds.close())
      dataStreams = []
    }
  }



}
