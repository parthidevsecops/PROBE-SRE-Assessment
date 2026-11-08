import React from "react";
import "../ChatBox.css";
import { animations } from "react-animation";
const VideoReply = (props) => {
  return (
    <div
      key={props.index}
      className="responseContainer"
      style={{ animation: animations.popIn }}
    >
      <div className="replyBot">
        <p>{props.text}</p>
      </div>
    </div>
  );
};

export default VideoReply;
