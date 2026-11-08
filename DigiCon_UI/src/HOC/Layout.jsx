import React, { Component } from "react";
import NavBar from "../Components/NavBar/NavBar";
import classes from "./Layout.css";
class Layout extends Component {
  render() {
    // console.log(this.props);
    return (
      <React.Fragment>
        <NavBar />
        <main className={classes.Content}>{this.props.children}</main>
      </React.Fragment>
    );
  }
}

export default Layout;
