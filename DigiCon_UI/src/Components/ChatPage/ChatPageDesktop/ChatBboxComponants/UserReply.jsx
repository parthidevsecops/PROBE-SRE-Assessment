import React from "react";
import "../ChatBox.css";
import { animations } from "react-animation";
import Avtar from "./AvtarChat";
import user from "../../../../assets/user.png";
const UserReply = (props) => {
  return (
    <div
      key={props.index}
      className="userContainer"
      style={{ animation: animations.popIn }}
    >
      <div className="chatUser">
        <p>{props.text}</p>
      </div>
      <Avtar icon={user} />
    </div>
  );
};

export default UserReply;
