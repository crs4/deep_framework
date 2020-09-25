'use strict';
var angular = require('../../../node_modules/@bower_components/angular')
angular.module('app')
  .service('dataService', ['$window',
    dataService
  ]);
console.log('Hyperpeer ...')
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
function dataService($window) {
  const hostname = location.hostname;
  console.log(hostname)
  const serverAddress = `wss://${hostname}:8000`; //156.148.132.107
  let hp = null;
  const userType = 'web_client'
  const username = 'webClient' + Date.now()
  let availableServers = []
  let availableCameras = []
  let remotePeerType = 'stream_manager'
  let deepSourcePeerId = 'none'
  let localStream = null
  let remoteStream = null
  let deepVideoSource = 'none'
  let remotePeer = null
  return {
    getConnection: () => hp,
    getLocalStream: () => localStream,
    getRemoteStream: () => remoteStream,
    getRemotePeerType: () => remotePeerType,
    getDeepVideoSource: () => deepVideoSource,
    getRemotePeer: () => remotePeer,
    getMyPeerId: () => username,
    getServers: () => availableServers,
    getCameras: () => availableCameras,
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
    connect: function (callback) {
      $window.navigator.mediaDevices.getUserMedia(constraints)//{ video: { width: 1280, height: 720 }, audio: true })
      .then((stream) => {
        localStream = stream
        let connected = false
        hp = new Hyperpeer(serverAddress, {
          id: username,
          type: userType,
          stream: stream,
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
            return callback(error)
          }
          alert(JSON.stringify(error))
        })
  
        hp.once('online', () => {
          availableServers = []
          availableCameras = []
          hp.getPeers()
          .then((peers) => {
            peers.forEach((peer) => {
              if (peer.busy) return
              if (peer.type === 'stream_manager') {
                availableServers.push(peer)
              } else if (peer.type === 'stream_capture') {
                availableCameras.push(peer)
              } 
            })
            callback(null, localStream)
            connected = true
          })
          .catch((error) => {
            console.error(error)
            callback(error)
          });
        })
  
        hp.on('close', () => {
          stream.getTracks().forEach(track => track.stop())
          setTimeout(() => {
            console.log('Connection ends')
            hp.removeAllListeners()
            hp = null
          }, 0.01)
        })
  
        hp.on('connection', () => {
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
      .catch((error) => {
        //callback(error)  
        console.log(error)
        constraints = { video: { width: 1280, height: 720, frameRate: 10 }, audio: true }   
        this.connect(callback)   
      });
    },
    start: function(callback) {
      if (!hp || !remotePeer) return;
      hp.connectTo(remotePeer.id)
      .then(() => {
        hp.once('connect', () => {
          hp.send({ type: 'source', peerId: deepSourcePeerId })
        })
      })
      .catch((error) => callback(error))

      hp.once('stream', (s) => {
        remoteStream = s
        console.log('remote stream: ' + s.id + '. Active: ' + s.active)
        callback(null, remoteStream)
      })
    },
    stop: function() {
      hp.disconnect()
      deepVideoSource = 'none'
    },
    setDeepVideoSource: function(sourcePeerId) {
      if (!hp || sourcePeerId === 'none' || deepSourcePeerId == sourcePeerId) return
      deepVideoSource = sourcePeerId
      hp.send({ type: 'source', peerId: sourcePeerId })
      hp.send({ type: 'metadata', metadata: { type: 'browser_video'} })
    },
    setRemotePeerType: (peerType) => remotePeerType = peerType,
    setRemotePeer: (peer) => remotePeer = peer
  };



}
