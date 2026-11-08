import React from "react";
import AppBar from "@material-ui/core/AppBar";
import Toolbar from "@material-ui/core/Toolbar";
import Button from "@material-ui/core/Button";
import Typography from "@material-ui/core/Typography";
import Box from "@material-ui/core/Box"; //InputBase,
import { makeStyles } from "@material-ui/core/styles";
import MenuIcon from "@material-ui/icons/Menu";
import NotificationsIcon from "@material-ui/icons/Notifications";
import Drawer from "@material-ui/core/Drawer";
import IconButton from "@material-ui/core/IconButton";
import ChevronLeftIcon from "@material-ui/icons/ChevronLeft";
import Menu from "@material-ui/core/Menu";
import MenuItem from "@material-ui/core/MenuItem";
// import Divider from "@material-ui/core/Divider";
import PowerSettingsNewIcon from "@material-ui/icons/PowerSettingsNew";
import { Redirect } from "react-router-dom";
import Badge from "@material-ui/core/Badge";
import List from "@material-ui/core/List";
import DrawerItem from "./DrawerItem";
// import DashboardIcon from "@material-ui/icons/Dashboard";
// import BarChartIcon from "@material-ui/icons/BarChart";
// import VideoLibraryIcon from "@material-ui/icons/VideoLibrary";
// import PhotoLibraryIcon from "@material-ui/icons/PhotoLibrary";
// import SlideshowIcon from "@material-ui/icons/Slideshow";
import clsx from "clsx";
const drawerWidth = 200;
const useStyles = makeStyles((theme) => ({
  root: {
    display: "flex",
  },
  menuButton: {
    marginRight: 36,
  },
  menuButtonHidden: {
    display: "none",
  },
  drawerPaper: {
    backgroundColor: "#d8dcd6",
    color: "#000",
    position: "absolute",
    whiteSpace: "nowrap",
    width: drawerWidth,
    // marginRight: 90,
    borderBottomRightRadius: 22,
    borderTopRightRadius: 22,
    // borderTop: 5,
    transition: theme.transitions.create("width", {
      easing: theme.transitions.easing.sharp,
      duration: theme.transitions.duration.enteringScreen,
    }),
  },
  drawerPaperClose: {
    backgroundColor: "#8ad2e2",
    color: "#000",
    // overflowX: "hidden",
    // paddingRight: 60,
    transition: theme.transitions.create("width", {
      easing: theme.transitions.easing.sharp,
      duration: theme.transitions.duration.leavingScreen,
    }),
    width: 0,
    // width: theme.spacing(7),
    // [theme.breakpoints.up("sm")]: {
    //   width: theme.spacing(9),
    // },
  },
  toolbar: {
    paddingRight: 24, // keep right padding when drawer closed
  },
  toolbarIcon: {
    display: "flex",
    alignItems: "center",
    justifyContent: "flex-end",
    padding: "0 8px",
    ...theme.mixins.toolbar,
  },
  appBar: {
    // backgroundColor: "#005469",
    background:
      " linear-gradient(to right, #517fa4 0%, #243949  51%, #517fa4  100%)",

    zIndex: theme.zIndex.drawer + 3,
    transition: theme.transitions.create(["width", "margin"], {
      easing: theme.transitions.easing.sharp,
      duration: theme.transitions.duration.leavingScreen,
    }),
  },

  appBarShift: {
    // marginLeft: drawerWidth - 30,
    marginLeft: -20,
    zIndex: theme.zIndex.drawer + 3,
    background:
      " linear-gradient(to right, #517fa4 0%, #243949  51%, #517fa4  100%)",
    // width: `calc(100% - ${drawerWidth}px)`,
    transition: theme.transitions.create(["width", "margin"], {
      easing: theme.transitions.easing.sharp,
      duration: theme.transitions.duration.enteringScreen,
    }),
  },

  title: {
    fontFamily: "Comic Sans MS",
    flexGrow: 1,
    display: "none",
    // margin: `calc(100% - ${drawerWidth}px)`,
    marginLeft: 0,
    [theme.breakpoints.up("sm")]: {
      display: "block",
    },
    fontSize: 28,
  },
  // titleShift: {
  //   flexGrow: 1,
  //   display: "none",
  //   // margin: `calc(100% - ${drawerWidth}px)`,
  //   marginLeft: 210,
  //   transition: theme.transitions.create(["width", "margin"], {
  //     easing: theme.transitions.easing.sharp,
  //     duration: theme.transitions.duration.enteringScreen,
  //   }),
  //   [theme.breakpoints.up("sm")]: {
  //     display: "block",
  //   },
  //   fontSize: 25,
  // },
  logoutButtoon: {
    height: 28,
    width: 28,
  },
  logoutText: {
    fontSize: 17,
  },
  logout: {
    // margin: "auto",
    float: "left",
  },
  button: {
    fontSize: 17,
  },
  task: {
    textAlign: "center",
    fontSize: 25,
    color: "#000",
    fontWeight: "bold",
    fontFamily: "Candara",
  },
}));

export default function SearchAppBar(props) {
  const classes = useStyles();
  const [logIn, SetLogIn] = React.useState(true);
  const [popupAnchor, setPopupAnchor] = React.useState(null);
  const [popupTarget, setPopupTarget] = React.useState(null);

  const isPopupOpen = Boolean(popupAnchor);
  const handleNavItemClick = (name, event) => {
    if (name === "Agent Orchestration") {
      setPopupAnchor(event.currentTarget);
      setPopupTarget(name);
      return;
    }
    props.handelDrawerClick(name);
  };

  const handlePopupClose = () => {
    setPopupAnchor(null);
    setPopupTarget(null);
  };

  const handlePopupChoice = (option) => {
    handlePopupClose();
    if (option === 1) {
      window.open("http://127.0.0.1:5000", "_blank");
      
    }
  };

  const iconsUp = [
    { name: "Customer Presentation"},
    { name: "RFI/ RFP Support" },
    { name: "Magnum Guide" },
    { name: "About Us" },
    { name: "Feedback" },
    { name: "Agent Orchestration"}
  ];

  const upPart = iconsUp.map((i, index) => (
    <div className={classes.drawerItem}>
      <DrawerItem
        onItemClick={handleNavItemClick}
        index={index}
        value={i}
      ></DrawerItem>
    </div>
  ));
  const logout = () => {
    SetLogIn(false);
    localStorage.removeItem("token");
  };
  if (logIn === false) {
    return <Redirect to="/login" />;
  } else {
    return (
      <div className={classes.root}>
        <AppBar
          position="absolute"
          className={clsx(classes.appBar, props.open && classes.appBarShift)}
        >
          <Toolbar className={classes.toolbar}>
            <IconButton
              edge="start"
              color="inherit"
              aria-label="open drawer"
              onClick={props.handleDrawerOpen}
              className={classes.menuButton}
            >
              <MenuIcon />
            </IconButton>
            <Typography
              className={clsx(classes.title, props.open && classes.titleShift)}
              variant="h6"
              noWrap
            >
              DigiCon
            </Typography>
            <div className={classes.search}></div>
            <Box p={1.5} />
            <Button color="inherit" className={classes.button}>
              Blogs
            </Button>
            <Box p={1.5} />
            <Button color="inherit" className={classes.button}>
              Sample FAQ
            </Button>
            <Box p={1.5} />
            {/* <Button color="inherit" className={classes.button}>
              About Us
            </Button> */}
            <Box p={1.5} />
            <IconButton
              aria-label="show 17 new notifications"
              color="inherit"
              onClick={props.handelNotication}
            >
              <Badge badgeContent={props.count} color="secondary">
                <NotificationsIcon />
              </Badge>
            </IconButton>
            <Box p={1.5} />
            <div>
              <IconButton
                edge="start"
                className={classes.menuButton}
                color="inherit"
                aria-label="open drawer"
                onClick={logout}
              >
                <PowerSettingsNewIcon className={classes.logoutButtoon} />
              </IconButton>
            </div>
          </Toolbar>
        </AppBar>
        <Drawer
          variant="permanent"
          classes={{
            paper: clsx(
              classes.drawerPaper,
              !props.open && classes.drawerPaperClose
            ),
          }}
          open={props.open}
        >
          <div className={classes.toolbarIcon}>
            <IconButton onClick={props.handleDrawerClose}>
              <ChevronLeftIcon className={classes.icon} />
            </IconButton>
          </div>
          <Box pt={6} />
          <div className={classes.task}> Tasks</div>
          <Box pt={2} />
          {/* <Divider /> */}
          <div className={classes.drawerList}>
            <List>{upPart}</List>
          </div>
        </Drawer>
        <Menu
          open={isPopupOpen}
          anchorEl={popupAnchor}
          onClose={handlePopupClose}
          anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
          transformOrigin={{ vertical: "top", horizontal: "center" }}
          getContentAnchorEl={null}
        >
          <MenuItem onClick={() => handlePopupChoice(1)}>Holmes</MenuItem>
          <MenuItem onClick={() => handlePopupChoice(2)}>Reparo</MenuItem>
        </Menu>
      </div>
    );
  }
}
