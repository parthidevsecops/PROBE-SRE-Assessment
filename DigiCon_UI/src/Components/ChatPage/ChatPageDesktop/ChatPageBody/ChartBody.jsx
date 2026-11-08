import React, { useEffect, useState } from "react";
import { Bar } from "react-chartjs-2";
const ChartBody = (props) => {
  // let [label, setLabel] = useState([]);
  // let [pass, setPass] = useState([]);
  // let [fail, setFail] = useState([]);
  // const label = props.data.map((i) => {
  //   // label1.push(i.Date);

  //   return i.Date;
  // });
  // const pass = props.data.map((i) => {
  //   // label1.push(i.Date);

  //   return i.Pass;
  // });
  // const fail = props.data.map((i) => {
  //   // label1.push(i.Date);

  //   return i.Fail;
  // });
  // let pass = [];
  // let fail = [];

  // shwo me the status of jenkins job
  // useEffect(() => {
  //   let label1 = [];
  //   let pass1 = [];
  //   let fail1 = [];
  //   let value = props.data.map((i) => {
  //     label1.push(i.Date);
  //     pass1.push(i.Pass);
  //     fail1.push(i.Fail);
  //     return [label1, pass1, fail1];
  //   });
  //   // setLabel(value[0]);
  //   // setPass(value[1]);
  //   // setFail(value[2]);
  //   console.log(`--------------------------------> ${value[0]}`);
  //   // label = value[0];
  //   // pass = value[1];
  //   // fail = value[2];
  // }, [props.data]);

  let data = {
    labels: props.data.label,
    datasets: [
      {
        label: "Pass",
        backgroundColor: "#009FFD",
        data: props.data.pass,
      },
      {
        label: "Fail",
        backgroundColor: "#f88379",
        data: props.data.fail,
      },
    ],
  };

  return (
    <div>
      <Bar
        data={data}
        options={{
          title: {
            display: true,
            text: "Status of javaPipeline Job",
            fontSize: 20,
          },
          legend: {
            display: true,
            position: "right",
          },
        }}
      />
    </div>
  );
};

export default ChartBody;
