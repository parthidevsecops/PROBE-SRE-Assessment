import React from "react";
import "../ChatBox.css";
import { makeStyles } from "@material-ui/core/styles";
import Avatar from "@material-ui/core/Avatar";

const useStyles = makeStyles((theme) => ({
  small: {
    width: theme.spacing(5),
    height: theme.spacing(5),
    background: "linear-gradient(to right, #2b5876  10%, #4e4376 100%)",
  },
}));

const HeadPart = (props) => {
  const classes = useStyles();
  return <Avatar className={classes.small} src={props.icon}></Avatar>;
};

export default HeadPart;
