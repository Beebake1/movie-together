// console.log('hello')

const btn = document.querySelectorAll('.btn');
const search = document.querySelectorAll('input');
for(let i=0; i < btn.length; i++){
    btn[i].addEventListener('click', function(e){
        e.preventDefault();
        let movieName = search[i].value;
        console.log(movieName);
        // put your movie seaarch logic
        // if()
         location.href = './list.html';
    })
}
// list

