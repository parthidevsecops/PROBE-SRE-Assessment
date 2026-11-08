import { makeStyles } from "@material-ui/core";
import React from "react";
import "./ListBody.css";

const useStyles = makeStyles((theme) => ({
  root: {
    padding: 10,
    margin: 30,
    fontSize: "1.125rem",
  },
}));

const ListBody = (props) => {
  const classes = useStyles();
  const list = props.list.split(",");
  const data = list.map((i, index) => {
    return (
      <li className="liclass" key={index}>
        {i}
      </li>
    );
  });
  return (
    <div className="root">
      <h3 className="head">What is Magnum? </h3>
      <ui className="ui">{data}</ui>
    </div>
  );
};

export default ListBody;
