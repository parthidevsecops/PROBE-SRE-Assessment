// PROBE SRE deployment: no Rasa/Ansible backend is deployed alongside this
// app. These are kept as loopback (not a public IP) so the legacy socket.io
// connections in Container.js fail locally instead of reaching an external
// server. The real chat path is /query, served same-origin by api.py.
const Ip = "127.0.0.1";
const AnsibleIP = "127.0.0.1";
const baseurl = `http://${Ip}:5000/`;
const baseurlVideo = `http://${Ip}:5000`;
const apiUrl = {
  baseurl: baseurl,
  baseurlVideo: baseurlVideo,
  ansible: `http://${AnsibleIP}:8090/`,
  chatApi: baseurl + "chat",
  videoApi: baseurl + "video",
};
export default apiUrl;
