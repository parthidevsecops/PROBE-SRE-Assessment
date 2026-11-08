import React from "react";
import "../ChatBox.css";
import ListItem from "@material-ui/core/ListItem";
import ListItemText from "@material-ui/core/ListItemText";
import GetAppIcon from "@material-ui/icons/GetApp";
import ListItemSecondaryAction from "@material-ui/core/ListItemSecondaryAction";
import ListItemAvatar from "@material-ui/core/ListItemAvatar";
import IconButton from "@material-ui/core/IconButton";
import List from "@material-ui/core/List";
import { makeStyles } from "@material-ui/core/styles";
import { animations } from "react-animation";

import api from "../../../../Service/api";

const useStyles = makeStyles((theme) => ({
  root: {
    backgroundImage: "linear-gradient(to right, #434343   0%, #000000  100%)",
    borderRadius: 20,
    color: "#fff",
  },
  icon: {
    color: "#fff",
  },
}));

const DocumentReply = (props) => {
  const classes = useStyles();
  return (
    <div className="document" style={{ animation: animations.popIn }}>
      <List dense="true" classes={{ root: classes.root }}>
        <ListItem>
          <ListItemAvatar>
            <img src={props.Icon} alt="pdf" className="image" />
          </ListItemAvatar>
          <ListItemText
            className={classes.icon}
            primary={props.name}
            // secondary="No Viruses"
          />
          <ListItemSecondaryAction>
            <IconButton
              edge="end"
              aria-label="download"
              href={api.baseurlVideo + props.text}
              //   onClick={() => download(props.text)}
            >
              <GetAppIcon fontSize="small" className={classes.icon} />
            </IconButton>
          </ListItemSecondaryAction>
        </ListItem>
      </List>
    </div>
  );
};

export default DocumentReply;
