import React from "react";
import ListItem from "@material-ui/core/ListItem";
// import ListItemIcon from "@material-ui/core/ListItemIcon";
import ListItemText from "@material-ui/core/ListItemText";
import { makeStyles } from "@material-ui/core/styles";
import "./drawerItem.css";

const useStyle = makeStyles((theme) => ({
  root: {
    flexGrow: 1,
  },

  icon: {
    color: "#fff",
  },
  text: {
    color: "#000",
    // padding: 0,
    marginLeft: -8,
    fontWeight: "bold",
  },
  listItemText: {
    fontSize: "14px",
    paddingTop: 13,
    marginTop: 5,
    paddingBottom: 13,
    justifyItems: "center",
    textAlign: "center",
    backgroundColor: "#9966cc",
    borderRadius: 10,
    wordWrap: "break-word",
    // overflow: "hidden",
    boxShadow:
      " 0 2.8px 2.2px rgba(0, 0, 0, 0.034), 0 6.7px 5.3px rgba(0, 0, 0, 0.048), 0 12.5px 10px rgba(0, 0, 0, 0.06), 0 22.3px 17.9px rgba(0, 0, 0, 0.072), 0 41.8px 33.4px rgba(0, 0, 0, 0.086), 0 100px 80px rgba(0, 0, 0, 0.12)",
  },
  item: {},
  OnClickitem: {
    borderTopLeftRadius: 25,
    borderBottomLeftRadius: 25,

    backgroundColor: "#fff",
  },
}));
const DrawerItem = (props) => {
  const classes = useStyle();
  return (
    <ListItem
      // className={classes.OnClickitem}
      button
      onClick={(event) => props.onItemClick(props.value.name, event)}
    >
      {/* <ListItemIcon className={classes.icon}>{props.value.icon}</ListItemIcon> */}
      <ListItemText
        classes={{ primary: classes.listItemText }}
        className={classes.text}
        primary={props.value.name}
      />
    </ListItem>
  );
};

export default DrawerItem;
