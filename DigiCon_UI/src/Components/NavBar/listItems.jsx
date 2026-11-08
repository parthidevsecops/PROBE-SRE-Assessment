import React from "react";
import ListItem from "@material-ui/core/ListItem";
import ListItemIcon from "@material-ui/core/ListItemIcon";
import ListItemText from "@material-ui/core/ListItemText";
import DashboardIcon from "@material-ui/icons/Dashboard";
import BarChartIcon from "@material-ui/icons/BarChart";
import VideoLibraryIcon from "@material-ui/icons/VideoLibrary";
import PhotoLibraryIcon from "@material-ui/icons/PhotoLibrary";
import SlideshowIcon from "@material-ui/icons/Slideshow";
export const mainListItems = (
  <div>
    <ListItem button>
      <ListItemIcon>
        <DashboardIcon />
      </ListItemIcon>
      <ListItemText primary="Logs" />
    </ListItem>
    <ListItem button>
      <ListItemIcon>
        <VideoLibraryIcon />
      </ListItemIcon>
      <ListItemText primary="Videos" />
    </ListItem>
    <ListItem button>
      <ListItemIcon>
        <PhotoLibraryIcon />
      </ListItemIcon>
      <ListItemText primary="Photos" />
    </ListItem>
    <ListItem button>
      <ListItemIcon>
        <SlideshowIcon />
      </ListItemIcon>
      <ListItemText primary="Slides" />
    </ListItem>
    <ListItem button>
      <ListItemIcon>
        <BarChartIcon />
      </ListItemIcon>
      <ListItemText primary="Charts" />
    </ListItem>
  </div>
);
