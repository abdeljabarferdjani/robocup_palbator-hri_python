import React, { Component } from 'react';
import Article from './Article';export default class ArticleList extends Component {
    render() {
       return (
          <div className='ui unstackable items'>
             <Article />
          </div>)
    }
}