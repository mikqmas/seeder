import React from 'react'
import ReactDOM from 'react-dom'
import Faker from 'faker'

function Test() {
  let test = "hello"
  return (
    <div>{test}</div>
  )
}

document.addEventListener('DOMContentLoaded', () => {
  ReactDOM.render(
    <Test />,
    document.getElementById('root')
  )
})
