import LoginPage from "../Components/LoginPage/LoginPage";
import LoginPageMobile from "../Components/LoginPage/LoginPageMobile";
import MobileViwe from "../Service/DetectMobile";
import { Redirect } from "react-router-dom";
import React, { Component } from "react";
class LoginPageContainer extends Component {
  constructor(props) {
    super(props);
    const token = localStorage.getItem("token");
    let loggedIn = true;
    if (token == null) {
      loggedIn = false;
    }
    this.state = {
      username: "",
      password: "",
      loggedIn,
      errorTextUsername: "",
      errorTextPassword: "",
      padding: 1.8,
    };
    this.onChange = this.onChange.bind(this);
    this.submitForm = this.submitForm.bind(this);
  }

  onChange(e) {
    this.setState({
      [e.target.name]: e.target.value,
    });
  }

  submitForm(e) {
    e.preventDefault();
    const { username, password } = this.state;

    if (username === "") {
      console.log(username);
      this.setState({
        errorTextUsername: "Username can't be empty",
        padding: 3,
      });
    } else if (password === "") {
      this.setState({
        errorTextPassword: "Password can't be empty",
        errorTextUsername: "",
        padding: 1.8,
      });
    } else {
      if (username === "admin" && password === "admin") {
        localStorage.setItem("token", "cawufxdoiqe7ftdwfa");
        this.setState({
          loggedIn: true,
        });
      } else {
        this.setState({
          errorTextUsername: "Username or Password Inavalid",
          errorTextPassword: "Username or Password Inavalid",
          padding: 3,
        });
      }
    }
  }
  render() {
    if (this.state.loggedIn) {
      return <Redirect to="/chat" />;
    } else if (MobileViwe.any()) {
      return <LoginPageMobile />;
    } else
      return (
        <LoginPage
          onChangeHandler={this.onChange}
          onSubmitHandler={this.submitForm}
          errorTextUsername={this.state.errorTextUsername}
          errorTextPassword={this.state.errorTextPassword}
          padding={this.state.padding}
        />
      );
  }
}

export default LoginPageContainer;
