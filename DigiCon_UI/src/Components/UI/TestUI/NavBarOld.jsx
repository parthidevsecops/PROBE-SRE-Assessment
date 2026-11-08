import React, { Component } from "react";
import { Redirect } from "react-router-dom";
import Button from "@material-ui/core/Button";
import ExitToAppRoundedIcon from "@material-ui/icons/ExitToAppRounded";
import "./NavBar.css";
import { Navbar, Nav } from "react-bootstrap";
import MobileView from "../../../Service/DetectMobile";
class NavBar extends Component {
  constructor(props) {
    super(props);
    let loggedIn = true;
    this.state = {
      loggedIn,
    };
    this.logout = this.logout.bind(this);
  }

  logout() {
    this.setState({
      loggedIn: false,
    });
  }

  render() {
    if (this.state.loggedIn === false) {
      localStorage.removeItem("token");
      return <Redirect to="/login" />;
    }
    let navData = (
      <React.Fragment>
        {" "}
        <Nav className="mr-auto">
          <Nav.Link href="#home">Home</Nav.Link>
        </Nav>
        <Button
          // className="float-right  mr-4"
          onClick={this.logout}
          variant="contained"
          color="primary"
          startIcon={<ExitToAppRoundedIcon />}
        >
          Logout
        </Button>
      </React.Fragment>
    );
    if (MobileView.any()) {
      navData = (
        <React.Fragment>
          {" "}
          <Nav className="mr-auto">
            <Nav.Link href="#home">Home</Nav.Link>
          </Nav>
          <Nav className="mr-auto">
            <Nav.Link href="#home">Chat Page</Nav.Link>
          </Nav>
          <Button onClick={this.logout} startIcon={<ExitToAppRoundedIcon />}>
            Logout
          </Button>
        </React.Fragment>
      );
    }
    return (
      <Navbar expand="lg" style={{ backgroundColor: "#617287" }}>
        <Navbar.Brand href="#home">DigiCon</Navbar.Brand>
        <Navbar.Toggle aria-controls="basic-navbar-nav" />
        <Navbar.Collapse id="basic-navbar-nav">{navData}</Navbar.Collapse>
      </Navbar>
    );
  }
}

export default NavBar;
