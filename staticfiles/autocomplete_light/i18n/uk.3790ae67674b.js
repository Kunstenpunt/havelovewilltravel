/*! Select2 4.0.13 | https://github.com/select2/select2/blob/master/LICENSE.md */
var dalLoadLanguage=function(n){var e;n&&n.fn&&n.fn.select2&&n.fn.select2.amd&&(e=n.fn.select2.amd),e.define("select2/i18n/uk",[],function(){function e(n,e,t,u){return 10<n%100&&n%100<15?u:n%10==1?e:1<n%10&&n%10<5?t:u}return{errorLoading:function(){return"Неможливо завантажити результати"},inputTooLong:function(n){return"Будь ласка, видаліть "+(n.input.length-n.maximum)+" "+e(n.maximum,"літеру","літери","літер")},inputTooShort:function(n){return"Будь ласка, введіть "+(n.minimum-n.input.length)+" або більше літер"},loadingMore:function(){return"Завантаження інших результатів…"},maximumSelected:function(n){return"Ви можете вибрати лише "+n.maximum+" "+e(n.maximum,"пункт","пункти","пунктів")},noResults:function(){return"Нічого не знайдено"},searching:function(){return"Пошук…"},removeAllItems:function(){return"Видалити всі елементи"}}}),e.define,e.require},event=new CustomEvent("dal-language-loaded",{lang:"uk"});document.dispatchEvent(event);