import React from "react";
import VideoBody from "./VideoBody";
import TextBody from "./TextBody";
// import PdfBody from "./PdfBody";
import ImageBody from "./ImageBody";
import ChartBody from "./ChartBody";
import DefaultBody from "./DefaultBody";
import LogBody from "./LogBody";
import ListBody from "./ListBody";

const BottomBody = (props) => {
  switch (props.currentIndex) {
    case -1:
      return <DefaultBody />;
    case 0:
      return <TextBody />;
    case 1:
      return <VideoBody videoUrl={props.videoUrl} />;
    case 2:
      return <ImageBody videoUrl={props.videoUrl} />;
    case 4:
      return <ChartBody data={props.videoUrl} />;
    case 5:
      return <LogBody Logs={props.Logs} />;
    case 6:
      return <ListBody list={props.videoUrl} />;
    default:
      return <DefaultBody />;
  }
  // if (props.currentIndex === -1) {
  //   return <DefaultBody />;
  // } else if (props.currentIndex === 0) {
  //   return <TextBody />;
  // } else if (props.currentIndex === 1) {
  //   return <VideoBody videoUrl={props.videoUrl} />;
  // } else if (props.currentIndex === 2) {
  //   return <ImageBody />;
  // } else if (props.currentIndex === 3) {
  //   return <PdfBody />;
  // } else if (props.currentIndex === 4) {
  //   return <ChartBody />;
  // } else if (props.currentIndex === 5) {
  //   return <LogBody Logs={props.Logs} />;
  // } else {
  //   return <TextBody />;
  // }
};

export default BottomBody;
