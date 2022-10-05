let activity = 0;
let activFloor = [];

let LANGUAG = {};
let nodeData = {};

//GET-запит 
function getURL(url){
	return new Promise(function(resolve, reject) {
		let xhr = new XMLHttpRequest();
		xhr.open('GET', url, true);
		xhr.onload = function() {
			if (this.status == 200) {
				resolve(xhr.response);
			} else {
				let error = new Error(this.statusText);
				error.code = this.status;
				reject(error);
			}
		};
		xhr.onerror = function() {reject(new Error("Network Error"));};
		xhr.send();
	});
}

// POST-send
function postURL(url, data){
	return new Promise(function(resolve, reject) {
		let xhr = new XMLHttpRequest();
		xhr.open('POST', url, true);
		xhr.setRequestHeader("Content-Type", "application/json");
		xhr.onload = function() {
			if (this.status == 200) {
				resolve(xhr.response);
			} else {
				let error = new Error(this.statusText);
				error.code = this.status;
				reject(error);
			}
		};
		xhr.onerror = function() {reject(new Error("Network Error"));};
		xhr.send(JSON.stringify(data));
	});

	// let xhr = new XMLHttpRequest();
	// xhr.open('POST', url, true);
	// xhr.setRequestHeader("Content-Type", "application/json");
	// xhr.onreadystatechange = function() {
	// 	if (this.readyState != 4) return;
	// 	// console.log(this.responseText);
	// }
	// let body = JSON.stringify(data);
	// xhr.send(body);
}

//відправка POST JSON для збереження змін строки в БД
function sendData(obj){
	let parentKey = obj.parentNode.parentNode.parentNode.id.split('_')[1]
	// console.log(parentKey)
	let formdata = document.getElementsByClassName("form");
	// let formdata = document.querySelectorAll("input.changedata");
	console.log(formdata);

	// let newData = {};
	for (let i=0 ; i<formdata.length; i++){
		let path = formdata[i].name.split('.');
		if (parentKey != undefined &&  parentKey != path[0]){
			continue;
		}
		let valdata = formdata[i].value;
		if (formdata[i].type == 'checkbox'){
			if (formdata[i].checked){valdata = 1;}
			else {valdata = 0;}
		}
		if (formdata[i].tagName == 'IMG'){valdata = formdata[i].alt;}

		switch (path.length){
			default:
				nodeData[path[0]] = valdata;
				break;
			case 2:
				nodeData[path[0]][path[1]] = valdata;
				break;
			case 3:
				nodeData[path[0]][path[1]][path[2]] = valdata;
				break;
		}
	};
	// console.log(nodeData);
	
	// postURL(LANGUAG.menu[activity].rest + '/save', nodeData)
	// .then(response => {
	// 	createActivity();
	// });
}

// завантаження локалі
function getLang(l){
	let url = './api/languag';
	if (l){url += '/' + l;}
	getURL(url)
	.then(response => {
		LANGUAG = JSON.parse(response);
		createActivity();
	})
}

// обробка натиснення кнопки "меню"
function menuShow(){
	let getDivObj = document.getElementById("menu")
	// console.dir(getDivObj)
	if (getDivObj.innerText == ""){
		let printDiv = '<hr>';
		for (let mid in LANGUAG.menu){
			// if (mid == 0){continue;};
			let menu = LANGUAG.menu[mid];
			// console.dir(menu)
			printDiv += `<div class="button menu" onclick="createActivity(${mid})">${menu.label}</div>`;
		}
		getDivObj.innerHTML = printDiv;
		getDivObj.hidden = false;
	}
	else {
		getDivObj.hidden = !getDivObj.hidden;
	}
}

// формування активіті
function createActivity(activID){
	// ховаємо список меню
	document.getElementById("menu").hidden = true;
	
	if (activID != undefined){
		activity = activID;
		activFloor = [];
	};
	
	let actinfo = LANGUAG.menu[activity]
	getURL(actinfo.rest)
	.then(
		response => {
			nodeData = JSON.parse(response);
			// if (unitdata.def_activ!=0 && activID == 0){
			// 	createActivity(unitdata.def_activ);
			// }
			createWall();
	},
		error => {
			// console.dir(error.code);
			if (error.code == 400){
				createWall();
			}
	});
}


// створення "стіни"
function createWall(){
	let labelDict = LANGUAG[LANGUAG.menu[activity].name]
	if (activity == 0){
		// element.innerHTML = `<img src="refresh.svg">`;
		document.getElementById("hederText").innerHTML = `<i>"${nodeData.pet.petname}"</i>`;
	}
	else{
		// element.innerHTML = `<img src="house.svg">`;
		document.getElementById("hederText").innerHTML = LANGUAG.menu[activity].label;
	}
	// console.dir(labelDict);
	let printDiv = '';
	if (activity == 2 || activity == 3){
		// schedule and settings
		for (let key in nodeData){
			printDiv += `<table><thead><th onclick="foldBricks('${key}')" align="left" width="35%"><span id="tree_${key}">&#10148;</span>&emsp;<u>`;
			if (activity == 2){
				printDiv += nodeData[key]['title'];
			}else{
				printDiv += labelDict[key].label;
			}
			printDiv +=`</u></th><th align="right" id="sw_${key}"></th></thead><tbody id="data_${key}" type="hidden"></tbody></table>`;
			};
		if (activity == 2){
			printDiv += `<div align="center"><img class="button big" onclick="newTask(this)" src="plus.svg"></div>`;
		}
	}
	else {
		// main and profile activity
		printDiv += '<table><tbody>';
		for (let key in labelDict){
			if (key == "buttons"){continue;}
			printDiv += '<tr><td>';
			if (labelDict[key].label!=undefined){printDiv += labelDict[key].label;}
			printDiv += '</td><td>';
			printDiv += creatBrick([key], labelDict[key], nodeData[key]) + '</td></tr>';
		};
		printDiv += `<tr style="background-color:#eeeeee00;"><td  align="center" colspan="2">`;
		let cmd_battons = LANGUAG["buttons"];
		if (labelDict.buttons != undefined){
			cmd_battons = labelDict.buttons;
		}
		for (let b in cmd_battons.data){
			btemp = cmd_battons.data[b];
			// console.dir(btemp);
			printDiv += `<div class="button ${cmd_battons.class}" onclick="${cmd_battons.data[b].onclick}">`;
			if (cmd_battons.data[b].img != undefined){
				printDiv += `<img class="big" src="${cmd_battons.data[b].img}"><br>`;
			}
			printDiv += `${cmd_battons.data[b].label}</div>`;
		}
		printDiv += `</td></tr>`;
		printDiv += '</tbody></table>';
	}
	document.getElementById("activity").innerHTML = printDiv;
	for (let i in activFloor){
		foldBricks(activFloor[i]);
	}
}


// розгортання/згортання "поверху"
function foldBricks(brick){
	let labelOob = LANGUAG[LANGUAG.menu[activity].name];
	if (activity == 3){
		labelOob = labelOob[brick];
	}
	// console.log(labelOob);
	
	// перемикач напроти групи налаштувань 
	let getBody = document.getElementById("sw_"+brick);
	if (getBody == null){
		return;
	}
	
	if (getBody.innerHTML == "" && labelOob.type != undefined){
		getBody.innerHTML = creatBrick([brick,'sw'], labelOob, nodeData[brick]);
	}
	else {
		getBody.innerHTML = "";
	}

	// таблиця з данними
	getBody = document.getElementById("data_"+brick);
	let printDiv = '';
	if (getBody.innerText == ""){
		// формування полів налаштування
		for (let key in labelOob.sett){
			if (key == "buttons"){continue;}
			printDiv += '<tr><td>';
			if (labelOob.sett[key].label!=undefined){printDiv += labelOob.sett[key].label;}
			printDiv += '</td><td>';
			printDiv += creatBrick([brick, key], labelOob.sett[key], nodeData[brick][key]) + '</td></tr>';
		}
		// формування кнопок керування
		printDiv += `<tr style="background-color:#eeeeee00;"><td  align="center" colspan="2">`;
		let cmd_battons = LANGUAG["buttons"];
		if (labelOob.buttons != undefined){cmd_battons = labelOob.buttons;}
		
		for (let b in cmd_battons.data){
			btemp = cmd_battons.data[b];
			// console.dir(btemp);
			printDiv += `<div class="button ${cmd_battons.class}" onclick="${btemp.onclick}">`;
			// if (btemp.img != undefined){
			// 	printDiv += `<img class="big" src="pet_food.svg"><br>`;
			// }
			printDiv += `${btemp.label}</div>`;
		}
		printDiv += `</td></tr>`;
		
		getBody.innerHTML = printDiv;
		getBody.hidden = false;
	}
	else {
		getBody.hidden = !getBody.hidden;
	}

	if (getBody.hidden){
		document.getElementById('tree_'+brick).innerHTML = '&#10148;';
		activFloor.splice(activFloor.indexOf(brick), 1);
	}else{
		document.getElementById('tree_'+brick).innerHTML = '&#9660;';
		if (activFloor.indexOf(brick) == -1){
			activFloor.push(brick);
		}
	}

	// console.log(activFloor)
}

// створення поля з данними
function creatBrick(name_arr, obj, data){
	if (data==undefined || data==''){data = '';}
	let inpname = name_arr.join('.');
	let bricksLine = '';
	let lock = '';
	if (obj.perm=='r'){lock = 'readonly';}
	else { lock = 'class="form"';}
	
	if (obj.type == "checkbox"){
		// console.dir(data);
		for (let cheklable in obj.data){
			let ch ='';
			if(data[cheklable]==1){ch = 'checked'};
			bricksLine += `<input type="checkbox" name="${inpname}.${cheklable}" ${ch} ${lock}>`;
			bricksLine += `<label>${obj.data[cheklable]}</label>&emsp;`;
		}
	}
	else if(obj.type == "select"){
		bricksLine += `<select class="form" name="${inpname}">`;
		for (let valkey in obj.data){
			let tmpo = `value="${valkey}"`;
			if (valkey == data){tmpo += " selected";}
			if (valkey == '0'){tmpo = "selected disabled";}
			bricksLine += `<option ${tmpo}>${obj.data[valkey]}</option>`;
		}
		bricksLine += '</select>';
	}
	else if (obj.type == "timest"){
		bricksLine += `<input type="text" name="${inpname}" ${lock} value="`;
		if (data.title != 'cron' && data.time != undefined){
			let datetime = new Date(data.time * 1000);
			let yy = "0" + datetime.getFullYear();
			let mn = "0" + (datetime.getMonth()+1);
			let dd = "0" + datetime.getDate();
			let hh = "0" + datetime.getHours();
			let mm = "0" + datetime.getMinutes();
			bricksLine += `${yy.substr(-4)}.${mn.substr(-2)}.${dd.substr(-2)} ${hh.substr(-2)}:${mm.substr(-2)}`;
			if (data.title){bricksLine += ` - ${data.title}`;}
		}
		bricksLine += '"></input>';
	}
	else if (obj.type == "switch"){
		let imgname = 'off.svg';
		if (data['on'] == 1){imgname = 'on.svg';}
		bricksLine += `<img class="form button smoll" onclick="channgSwitch(this)" alt="${data['on']}" name="${inpname}" src="${imgname}">`;
	}
	else{
		bricksLine +=`<input type="${obj.type}" name="${inpname}" `;
		if (obj.min !=undefined){bricksLine +=`min="${obj.min}" `;}
		if (obj.max !=undefined){bricksLine +=`max="${obj.max}" `;}
		bricksLine +=`value="${data}"${lock}>`;
	};

	return bricksLine;
}


function channgSwitch(obj){
	if (obj.alt == "1"){
		obj.src = "off.svg";
		obj.alt = "0";
	}
	else{
		obj.src = "on.svg";
		obj.alt = "1";	
	}
}

// add new task to schaduler
function newTask(){
	// console.log(nodeData)
	const d = new Date();
	let tid = "f"+d.getTime();
	let taskData = {"on":0,"title":"New feed","ftime":"06:00","wd":{"0":1,"1":1,"2":1,"3":1,"4":1,"5":1,"6":1},"portion":"2"};
	nodeData[tid] = taskData;
	createWall();
	foldBricks(tid);
}

function delData(obj){
	let parentKey = obj.parentNode.parentNode.parentNode.id.split('_')[1]
	delete nodeData[parentKey];
	postURL(LANGUAG.menu[activity].rest + '/save', nodeData)
	.then(response => {
		createActivity();
	});
}

function sendCMD(cmd){
	let url = './api/cmd/'+cmd;
	getURL(url)
	.then(response => {
		// console.log(response);
		createActivity();
	})
}