import React from "react";
import { Paper } from "@material-ui/core";
import "../../../../node_modules/video-react/dist/video-react.css";

const ChatBody = (props) => {
  return <Paper className="p-3  m-0">{props.children}</Paper>;
};

export default ChatBody;
