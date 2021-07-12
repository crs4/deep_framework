
:orphan:

.. _custom_web_app_label:

Custom web app example
----------------------

::

    const Hyperpeer = require('hyperpeer')
    const hostname = location.hostname
    const serverAddress = `wss://${hostname}:8000`

    // The <video> element to use for showing remote video, for this example the remote video is just mirroring the local video stream
    const video = document.getElementById('video')

    // Get local media video
    navigator.mediaDevices.getUserMedia({ video: true })
        .then((stream) => {
            // Instantiate Hyperpeer with an id, a type, the input media stream and the output <video> element
            const myPeerId = 'web_client' + Date.now()
            const deepPeer = new Hyperpeer(serverAddress, {
                id: myPeerId,
                type: 'web_client',
                stream: stream,
                videoElement: video
            })

            // Once get the 'online' event get the available peers
            deepPeer.on('online', () => {
                deepPeer.getPeers()
                    .then((peers) => {
                        // Check which peers are Stream Managers and which are Stream Capture (in this version there is only one Stream Manager and at most one Stream Capture)
                        peers.forEach((peer) => {
                            if (peer.busy) return
                            if (peer.type === 'stream_manager') {
                                availableServers.push(peer)
                            } else if (peer.type === 'stream_capture') {
                                availableCameras.push(peer)
                            }
                        })
                        // let's assume you want to inmediately connect to the first Stream Manager available
                        if (availableServers.length >= 1) {
                            return deepPeer.connectTo(availableServers[0])
                        }
                    })
                    .catch((error) => { alert(error) })
            })

            // Once connected indicate to Stream Manager the video stream to process, in this case it's set to 'myPeerId' on order to indicate the local webcam but you can give the id of one of the Stream Capture peers
            deepPeer.on('connect', () => {
                console.log('Peer-to-peer connection established!')
                deepVideoSource = sourcePeerId
                deepPeer.send({ type: 'source', peerId: myPeerId })
            })

            // On data handle the Stream Manager message
            deepPeer.on('data', (data) => {
                // All message are converted to javascript objects and have a 'type' property. Results have type 'data'
                if (data.type == 'data') {
                    // The information regading each detected face is contained inside an array also called data. Let's create a dictionary where the face id is the key and the value are its attributes
                    let faces = {}
                    data.data.forEach((face) => {
                        faces[face.id] = {
                            // The face bounding box is in the 'rect' attribute 
                            boundingBox: {
                                x_topleft: face.rect.x_topleft,
                                y_topleft: face.rect.y_topleft,
                                x_bottomright: face.rect.x_bottomright,
                                y_bottomright: face.rect.y_bottomright
                            },
                            // If the face recognition algorithm is running the 'face_recognition' attribute contains either the name of the person or the string 'Unknown'
                            name: face.face_recognition,
                            // If the gender algorithm is running the 'gender' attribute is either 'Male' or 'Female'
                            gender: face.gender,
                            // If the pitch algorithm is running the 'pitch' attribute is a number representing the horizontal orientation of the face
                            pitch: face.pitch,
                            // If the yaw algorithm is running the 'yaw' attribute is a number representing the vertical orientation of the face
                            yaw: face.yaw,
                            // If the age algorithm is running the 'age' attribute is a string representing the apparent age of the face
                            ageRange: face.age,
                            // If the emotion algorithm is running the 'emotion' attribute is an array of the possible emotions with its probabilities
                            emotions: face.emotion ? face.emotion.map(e => {
                                return {
                                    label: e[0],
                                    probability: e[1]
                                }
                            }) : [],
                            // If the glasses algorithm is running the 'glasses' attribute is 'glasses', 'sunglasses' or 'no glasses'
                            glasses: face.glasses
                        }
                    })
                    // In the current verion Stream Manager expects a message of type 'acknowledge' for each data message sent so it can calculate some stats
                    let acknowledge = {
                        type: 'acknowledge',
                        // It only needs the receive back the 'rec_time' attribute
                        rec_time: data.rec_time
                    }
                    deepPeer.send(acknowledge)
                } else if (data.type == 'warning') {
                    console.error('Deep warning' + JSON.stringify(data))
                } else if (data.type == 'error') {
                    alert('Deep error' + JSON.stringify(data))
                }
                else {
                    console.log('Deep message' + JSON.stringify(data))
                }
            })

            deepPeer.on('error', (error) => {
                alert('Hyperpeer Error: ' + error)
            })
        })
        .catch((error) => {
            alert('mediaDevices error: ' + error)
        })
