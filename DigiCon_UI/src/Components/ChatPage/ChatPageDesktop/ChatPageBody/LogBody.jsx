import { makeStyles } from "@material-ui/core/styles";
import React, { useEffect, useRef } from "react";
const useStyles = makeStyles((theme) => ({
  logs: {
    backgroundColor: "#000",
    padding: 10,
    color: "#fff",
    height: 500,
    fontFamily: "Arial",
    fontSize: 13,
    overflow: "scroll",
    // margin: 10,
  },
  log: {
    marginTop: 10,
  },
}));

const LogBody = (props) => {
  const classes = useStyles();
  const LogEndRef = useRef(null);
  const scrollToBottom = () => {
    LogEndRef.current.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [props.Logs]);
  const logData = props.Logs.map((i, index) => {
    return <p className={classes.log}>{i.log}</p>;
  });
  return (
    <div className={classes.logs}>
      {logData}
      <div ref={LogEndRef} />
    </div>
  );
};

export default LogBody;
