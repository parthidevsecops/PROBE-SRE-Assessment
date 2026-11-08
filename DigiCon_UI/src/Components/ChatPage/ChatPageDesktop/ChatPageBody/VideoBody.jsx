import React from "react";
import { Player } from "video-react";
import apiUrl from "../../../../Service/api";

export default (props) => {
  return (
    <Player
      playsInline
      poster="/assets/background.png"
      src={apiUrl.baseurlVideo + props.videoUrl}
    />
  );
};

// Video is streaming...
